'use strict';
/**
 * Hazard-avoiding route planner.
 *
 * The public OSRM server cannot "exclude an area", so we do it ourselves:
 *   1. ask OSRM for the normal route (+ its alternatives)
 *   2. find which known hazards (blocked roads / flooded underpasses) lie on it
 *   3. if any: force the route sideways through candidate waypoints placed
 *      either side of the hazard, re-route, and VERIFY the new geometry really
 *      stays clear of every hazard
 *   4. never fake a detour – if nothing clear is found we say so.
 *
 * `osrm(waypoints)` is injected so the logic can be unit-tested without network.
 *   osrm([[lat,lng], ...]) -> Promise<Array<{coords, distanceM, durationS, steps}>>
 *   (first element = best route, rest = alternatives; empty/throws if no route)
 */

const {
  haversineM,
  pointToPolylineM,
  pointToSegmentM,
  bearing,
  offsetPoint
} = require('./geo');

const DEFAULT_RADIUS_M = 300;
const SIDE_OFFSETS_M = [800, 1600, 3000, 5000];
const MAX_ROUNDS = 3;

/** Hazards that lie within radiusM of the route polyline. */
function hazardsOnRoute(coords, hazards, radiusM) {
  const hit = [];
  hazards.forEach((h, i) => {
    const r = pointToPolylineM([h.lat, h.lng], coords);
    if (r.dist <= radiusM) hit.push({ hazard: h, hazardIndex: i, distM: Math.round(r.dist), segment: r.index });
  });
  return hit;
}

/** Contiguous polyline pieces that pass within radiusM of any hazard (for drawing in red). */
function blockedSegments(coords, hazards, radiusM) {
  const segs = [];
  let cur = null;
  for (let i = 0; i < coords.length - 1; i++) {
    const near = hazards.some(
      h => pointToSegmentM([h.lat, h.lng], coords[i], coords[i + 1]).dist <= radiusM
    );
    if (near) {
      if (!cur) cur = [coords[i]];
      cur.push(coords[i + 1]);
    } else if (cur) {
      segs.push(cur);
      cur = null;
    }
  }
  if (cur) segs.push(cur);
  return segs;
}

/** Order waypoints by their progress along the from->to line. */
function sortAlong(from, to, wps) {
  return [...wps].sort(
    (a, b) => pointToSegmentM(a, from, to).t - pointToSegmentM(b, from, to).t
  );
}

function summarise(route) {
  return {
    coords: route.coords,
    distanceM: route.distanceM,
    durationS: route.durationS,
    steps: route.steps || []
  };
}

async function safeOsrm(osrm, wps) {
  try {
    const r = await osrm(wps);
    return Array.isArray(r) ? r.filter(x => x && x.coords && x.coords.length > 1) : [];
  } catch (_) {
    return [];
  }
}

/**
 * @param {object} p
 * @param {number[]} p.from [lat,lng]
 * @param {number[]} p.to   [lat,lng]
 * @param {{lat:number,lng:number,title?:string}[]} p.hazards
 * @param {number} [p.radiusM]
 * @param {Function} p.osrm
 */
async function planSafeRoute({ from, to, hazards = [], radiusM = DEFAULT_RADIUS_M, osrm }) {
  const directAll = await safeOsrm(osrm, [from, to]);
  if (directAll.length === 0) {
    return { status: 'no_route', message: 'No drivable road route found between these two points.' };
  }
  const direct = directAll[0];

  // A hazard AT the origin/destination cannot be avoided (e.g. "route to the flooded site").
  const endpointHazards = hazards.filter(
    h =>
      haversineM(from, [h.lat, h.lng]) <= radiusM + 400 ||
      haversineM(to, [h.lat, h.lng]) <= radiusM + 400
  );
  const avoidable = hazards.filter(h => !endpointHazards.includes(h));

  const onDirect = hazardsOnRoute(direct.coords, avoidable, radiusM);
  const base = {
    direct: summarise(direct),
    hazardsOnDirect: onDirect.map(o => ({ title: o.hazard.title || 'Hazard', lat: o.hazard.lat, lng: o.hazard.lng, distM: o.distM })),
    blockedSegments: blockedSegments(direct.coords, avoidable, radiusM),
    endpointHazards: endpointHazards.map(h => ({ title: h.title || 'Hazard', lat: h.lat, lng: h.lng })),
    radiusM
  };

  if (onDirect.length === 0) {
    return { ...base, status: 'clear', safe: summarise(direct), message: 'Direct route does not pass any known hazard.' };
  }

  // --- 1. alternatives that OSRM already returned and that are clear ---
  const clearAlts = directAll
    .slice(1)
    .filter(r => hazardsOnRoute(r.coords, avoidable, radiusM).length === 0);
  let best = clearAlts.sort((a, b) => a.durationS - b.durationS)[0] || null;

  // --- 2. sideways waypoint search ---
  if (!best) {
    let wps = [];
    let current = direct;
    let currentCount = onDirect.length;

    for (let round = 0; round < MAX_ROUNDS && currentCount > 0; round++) {
      const hits = hazardsOnRoute(current.coords, avoidable, radiusM).sort((a, b) => a.segment - b.segment);
      const target = hits[0].hazard;
      const tp = [target.lat, target.lng];
      const heading = bearing(from, to);
      const candidates = [];
      for (const d of SIDE_OFFSETS_M) {
        candidates.push(offsetPoint(tp, heading + Math.PI / 2, d));
        candidates.push(offsetPoint(tp, heading - Math.PI / 2, d));
      }

      const tried = await Promise.all(
        candidates.map(async c => {
          const set = sortAlong(from, to, [...wps, c]);
          const res = await safeOsrm(osrm, [from, ...set, to]);
          if (!res.length) return null;
          // pick the best of the returned routes for this waypoint set
          const scored = res
            .map(r => ({ r, n: hazardsOnRoute(r.coords, avoidable, radiusM).length }))
            .sort((a, b) => a.n - b.n || a.r.durationS - b.r.durationS)[0];
          return { wp: c, route: scored.r, count: scored.n };
        })
      );
      const valid = tried.filter(Boolean).sort((a, b) => a.count - b.count || a.route.durationS - b.route.durationS);
      if (valid.length === 0 || valid[0].count >= currentCount) break; // no progress
      wps = sortAlong(from, to, [...wps, valid[0].wp]);
      current = valid[0].route;
      currentCount = valid[0].count;
    }
    if (currentCount === 0) best = current;
  }

  if (!best) {
    return {
      ...base,
      status: 'no_safe_route',
      safe: null,
      message:
        'Could not find a drivable route that stays clear of all reported hazards. Do not rely on the direct route – verify on the ground or use another approach.'
    };
  }

  return {
    ...base,
    status: 'rerouted',
    safe: summarise(best),
    extraDistanceM: Math.round(best.distanceM - direct.distanceM),
    extraDurationS: Math.round(best.durationS - direct.durationS),
    message: 'Direct route crosses a reported hazard. A verified bypass was found.'
  };
}

module.exports = { planSafeRoute, hazardsOnRoute, blockedSegments, DEFAULT_RADIUS_M };
