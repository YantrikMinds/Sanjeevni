'use strict';
/**
 * Small geometry helpers (no dependencies). All points are [lat, lng].
 */

const R_EARTH_M = 6371008.8;
const rad = d => (d * Math.PI) / 180;

/** Haversine distance in metres. */
function haversineM(a, b) {
  const dLat = rad(b[0] - a[0]);
  const dLng = rad(b[1] - a[1]);
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dLng / 2) ** 2;
  return 2 * R_EARTH_M * Math.asin(Math.min(1, Math.sqrt(s)));
}

/** Haversine distance in km, one decimal (never rounds 2.5 km to 3 km). */
function distanceKm(lat1, lng1, lat2, lng2) {
  return Math.round(haversineM([lat1, lng1], [lat2, lng2]) / 100) / 10;
}

/** Local flat projection (metres) around a reference latitude – fine for <~100 km. */
function project(p, refLat) {
  return [rad(p[1]) * Math.cos(rad(refLat)) * R_EARTH_M, rad(p[0]) * R_EARTH_M];
}

/** Distance (m) from point p to segment a-b. Also returns the position t in [0,1]. */
function pointToSegmentM(p, a, b) {
  const ref = p[0];
  const P = project(p, ref);
  const A = project(a, ref);
  const B = project(b, ref);
  const dx = B[0] - A[0];
  const dy = B[1] - A[1];
  const len2 = dx * dx + dy * dy;
  let t = len2 === 0 ? 0 : ((P[0] - A[0]) * dx + (P[1] - A[1]) * dy) / len2;
  t = Math.max(0, Math.min(1, t));
  const cx = A[0] + t * dx;
  const cy = A[1] + t * dy;
  return { dist: Math.hypot(P[0] - cx, P[1] - cy), t };
}

/** Minimum distance (m) from p to a polyline, and the index of the closest segment. */
function pointToPolylineM(p, line) {
  let best = { dist: Infinity, index: -1 };
  for (let i = 0; i < line.length - 1; i++) {
    const d = pointToSegmentM(p, line[i], line[i + 1]).dist;
    if (d < best.dist) best = { dist: d, index: i };
  }
  if (line.length === 1) best = { dist: haversineM(p, line[0]), index: 0 };
  return best;
}

/** Initial bearing in radians from a to b (flat approximation). */
function bearing(a, b) {
  const A = project(a, a[0]);
  const B = project(b, a[0]);
  return Math.atan2(B[1] - A[1], B[0] - A[0]); // angle in the local x/y plane
}

/** Move point p by distM metres along direction angle (local x/y plane, radians). */
function offsetPoint(p, angle, distM) {
  const dLat = (Math.sin(angle) * distM) / R_EARTH_M;
  const dLng = (Math.cos(angle) * distM) / (R_EARTH_M * Math.cos(rad(p[0])));
  return [p[0] + (dLat * 180) / Math.PI, p[1] + (dLng * 180) / Math.PI];
}

/** Parse + validate a latitude/longitude pair. Returns null if invalid. */
function parseLatLng(lat, lng) {
  const la = Number(lat);
  const lo = Number(lng);
  if (lat === '' || lng === '' || lat == null || lng == null) return null;
  if (!Number.isFinite(la) || !Number.isFinite(lo)) return null;
  if (la < -90 || la > 90 || lo < -180 || lo > 180) return null;
  return [la, lo];
}

module.exports = {
  haversineM,
  distanceKm,
  pointToSegmentM,
  pointToPolylineM,
  bearing,
  offsetPoint,
  parseLatLng
};
