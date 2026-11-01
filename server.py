#!/usr/bin/env python3
"""
SANJEEVNI FIELD TACTICAL GATEWAY & SERVER
Rubble Edge Rover (phone) -> Tactical War Room (laptop)

Pure Python standard library. Runs fine on 1.8 GB RAM / Celeron.

Video path (fast + simple):
  phone  --POST /api/frame (JPEG bytes, detection in query)-->  server (keeps only the LATEST frame)
  laptop --GET  /api/frame.jpg?after=<seq> (long-poll)       -->  gets a new frame the moment it lands
  anything --GET /stream.mjpg                                 -->  classic MJPEG stream (optional)

Why it was slow before: HTTP/1.0 meant a brand new TLS handshake for EVERY request, and the
handshake ran on the accept (main) thread, so one stuck phone connection froze the whole server.
Now: HTTP/1.1 keep-alive + TLS handshake inside the per-connection worker thread.
"""

import http.server
import socketserver
import ssl
import json
import sqlite3
import os
import socket
import time
import hashlib
import threading
from urllib.parse import urlparse, parse_qs
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT_HTTPS = 8443
PORT_HTTP = 8080
DB_FILE = os.path.join(BASE_DIR, "sanjeevni.db")
CERT_FILE = os.path.join(BASE_DIR, "server.crt")
KEY_FILE = os.path.join(BASE_DIR, "server.key")

# Only these files can be fetched by name (the old fallback could serve server.key / the DB!)
PAGES = {
    "/": "dashboard.html",
    "/dashboard": "dashboard.html",
    "/rover": "rover.html",
    "/phone": "rover.html",
    "/3d-simulation": "3d_collapse_simulation.html",
    "/routing-map": "dynamic_routing_map.html",
}

FRAME_STALE_SEC = 2.5      # no frame for this long -> rover considered offline
MAX_FRAME_BYTES = 2 * 1024 * 1024

# ---------------------------------------------------------------- multi-device state
state_lock = threading.Lock()
frame_cond = threading.Condition()
frame = {"jpg": b"", "seq": 0, "t": 0.0}

devices = {}
active_device_id = "MOTO-G62"

def get_or_create_device(node_id):
    node_id = str(node_id or "MOTO-G62").strip().upper()
    if node_id not in devices:
        name = node_id
        loc = "Sector B-2 (Hotel Collapse Void)"
        lat, lng = 28.7041, 77.1025
        if "MOTO" in node_id:
            name = "Rover Alpha (Moto G62)"
            loc = "Sector B-2 (Grand Palace Hotel Void)"
            lat, lng = 28.7041, 77.1025
        elif "IPHONE" in node_id:
            name = "Rover Beta (iPhone 13)"
            loc = "Sector D-4 (Sunrise Apartments Block C)"
            lat, lng = 28.7058, 77.1042
        elif "NANO" in node_id or "ESP32" in node_id:
            name = "Sanjeevni Nano-Rover (ESP32-S3 Hardware)"
            loc = "Sector A-3 (Narrow Crevice Insertion)"
            lat, lng = 28.7048, 77.1028
        elif "ROVER" in node_id:
            name = f"Rover Unit ({node_id})"
            loc = "Sector A-1 (Commercial Complex)"
            lat, lng = 28.7082, 77.1011
        else:
            name = f"Rover ({node_id})"

        devices[node_id] = {
            "node_id": node_id,
            "name": name,
            "frame": {"jpg": b"", "seq": 0, "t": 0.0},
            "status": "OFFLINE",
            "fps": 0,
            "fps_count": 0,
            "fps_t0": time.time(),
            "sensors": {
                "tilt_deg": 5.0,
                "ch4_methane_ppm": 16,
                "co_ppm": 7,
                "battery_pct": 92,
                "void_clearance_m": 1.15
            },
            "detection": {"detected": False, "class": "None", "confidence": 0.0, "box": [0,0,0,0]},
            "location": loc,
            "lat": lat,
            "lng": lng,
            "last_seen": 0.0,
            "last_alert_time": 0.0
        }
    return devices[node_id]

# Pre-register default rovers
get_or_create_device("MOTO-G62")
get_or_create_device("IPHONE-13")
get_or_create_device("SANJEEVNI-NANO-01")

latest_rover_cmd = {"cmd": "stop", "spd": "180", "ip": "192.168.4.1", "time": 0.0}

detection_events = [
    {
        "id": "EVT-101",
        "device_id": "MOTO-G62",
        "device_name": "Rover Alpha (Moto G62)",
        "location": "Sector B-2 (Grand Palace Hotel Void)",
        "coordinates": "28.7041° N, 77.1025° E",
        "confidence": 88,
        "timestamp": "11:32:05",
        "type": "SURVIVOR DETECTED: HUMAN LIMB",
        "status": "AWAITING DISPATCH"
    }
]

def add_detection_event(node_id, name, location, lat, lng, confidence):
    ts = datetime.now().strftime("%H:%M:%S")
    evt = {
        "id": f"EVT-{int(time.time()*10)%10000}",
        "device_id": node_id,
        "device_name": name,
        "location": location,
        "coordinates": f"{lat:.4f}° N, {lng:.4f}° E",
        "confidence": confidence,
        "timestamp": ts,
        "type": "SURVIVOR DETECTED: HUMAN LIMB",
        "status": "AWAITING DISPATCH"
    }
    detection_events.insert(0, evt)
    if len(detection_events) > 30:
        detection_events.pop()

mission_targets = [
    {
        "id": "SEC-B2",
        "name": "Sector B-2: Grand Palace Hotel Collapse",
        "assigned_device": "MOTO-G62",
        "priority": "CRITICAL",
        "status": "SCANNING_NOW",
        "desc": "Sublevel crawlway void (Pancake Collapse)",
        "coordinates": "28.7041° N, 77.1025° E"
    },
    {
        "id": "SEC-D4",
        "name": "Sector D-4: Sunrise Residential Apartments (Block C)",
        "assigned_device": "IPHONE-13",
        "priority": "HIGH",
        "status": "EN_ROUTE",
        "desc": "Stairwell void pocket (Lean-To Collapse)",
        "coordinates": "28.7058° N, 77.1042° E"
    },
    {
        "id": "SEC-A1",
        "name": "Sector A-1: Metro Complex Underground Concourse",
        "assigned_device": "UNASSIGNED",
        "priority": "HIGH",
        "status": "PENDING_RECON",
        "desc": "Heavy structural debris, requires rover scouting",
        "coordinates": "28.7082° N, 77.1011° E"
    },
    {
        "id": "SEC-C3",
        "name": "Sector C-3: City Central Hospital South Wing",
        "assigned_device": "UNASSIGNED",
        "priority": "LOW",
        "status": "CLEARED",
        "desc": "Ground corridor verified clear for ambulances",
        "coordinates": "28.7015° N, 77.1065° E"
    }
]

latest_telemetry = devices["MOTO-G62"]["sensors"]
_last_db_log = 0.0


def calculate_priority(survivors, severity, access_risk):
    # Priority Score = (Survivors * 35 + Severity * 25) / Access Risk
    if access_risk <= 0:
        access_risk = 0.5
    return round((survivors * 35.0 + severity * 25.0) / float(access_risk), 1)


def _inc(id_, sector, source, survivors, severity, risk, status, ts, signoff=None):
    return {
        "id": id_, "sector": sector, "source": source,
        "survivors": survivors, "severity": severity, "access_risk": risk,
        "priority_score": calculate_priority(survivors, severity, risk),
        "status": status, "timestamp": ts, "signoff_hash": signoff,
    }


def default_incidents():
    return [
        _inc("INC-101", "Sector B-2 (Hotel Collapse Void)", "Rover Alpha (Moto G62)",
             0, 4, 2.2, "AWAITING ROVER SCAN", "16:42:10"),
        _inc("INC-102", "Sector D-4 (Residential Block C)", "Acoustic / Citizen SOS",
             1, 2, 3.8, "APPROVED", "16:15:00",
             "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        _inc("INC-103", "Sector A-1 (Commercial Complex Facade)", "Satellite ConvNeXt",
             0, 1, 1.1, "MONITORING", "15:50:00"),
    ]


incidents_db = default_incidents()


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, node_id TEXT,
        detection_class TEXT, confidence REAL, tilt_deg REAL, ch4_ppm REAL,
        co_ppm REAL, mesh_rssi INTEGER, has_snapshot INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, incident_id TEXT,
        commander TEXT, action TEXT, signoff_hash TEXT)''')
    conn.commit()
    conn.close()


def log_telemetry_throttled():
    """SQLite write at most every 2 s (was every request)."""
    global _last_db_log
    now = time.time()
    if now - _last_db_log < 2.0:
        return
    _last_db_log = now
    try:
        conn = sqlite3.connect(DB_FILE, timeout=2)
        det, sens = latest_telemetry["detection"], latest_telemetry["sensors"]
        conn.execute(
            "INSERT INTO telemetry (timestamp,node_id,detection_class,confidence,tilt_deg,ch4_ppm,co_ppm,mesh_rssi,has_snapshot)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (latest_telemetry["timestamp"], latest_telemetry["node_id"], det.get("class", "None"),
             det.get("confidence", 0.0), sens.get("tilt_deg", 0.0), sens.get("ch4_methane_ppm", 0.0),
             sens.get("co_ppm", 0.0), latest_telemetry["mesh_rssi"], 1 if frame["seq"] else 0))
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB log error:", e)


def apply_detection(det):
    """Update live detection + the rover's incident (INC-101)."""
    inc = incidents_db[0]
    latest_telemetry["detection"] = det
    if inc["signoff_hash"]:
        return  # already approved by commander: never overwrite the signed-off record
    if det.get("detected"):
        inc["survivors"] = 1
        inc["status"] = "SURVIVOR CONFIRMED - AWAITING COMMANDER"
    else:
        inc["survivors"] = 0
        inc["status"] = "SCANNING VOID"
    inc["priority_score"] = calculate_priority(inc["survivors"], inc["severity"], inc["access_risk"])


def current_telemetry():
    out = dict(latest_telemetry)
    age = time.time() - frame["t"] if frame["t"] else 999
    out["frame_age"] = round(age, 2)
    out["rover_online"] = age < FRAME_STALE_SEC
    out["status"] = "ACTIVE" if out["rover_online"] else "OFFLINE"
    if not out["rover_online"]:
        out["detection"] = {"detected": False, "class": "None", "confidence": 0.0, "box": [0, 0, 0, 0]}
        if not incidents_db[0]["signoff_hash"] and incidents_db[0]["survivors"]:
            apply_detection(out["detection"])
    return out


# ---------------------------------------------------------------- HTTP handler
class SanjeevniHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # keep-alive: one TLS handshake, many requests
    timeout = 30                    # idle keep-alive sockets get reaped
    server_version = "Sanjeevni/2.0"

    def log_message(self, fmt, *args):
        pass  # quiet: printing every request slows a Celeron down

    # -- helpers
    def _send(self, code, body=b"", ctype="text/plain", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Expose-Headers", "X-Seq, X-Det, X-Age")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body and self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, obj, status=200):
        self._send(status, json.dumps(obj).encode(), "application/json")

    def serve_file(self, name, ctype):
        path = os.path.join(BASE_DIR, name)
        if not os.path.isfile(path):
            return self._send(404, b"File not found")
        with open(path, "rb") as f:
            self._send(200, f.read(), ctype)

    # -- routes
    def do_OPTIONS(self):
        self._send(204, b"", extra={"Access-Control-Allow-Methods": "GET, POST, OPTIONS"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path, q = parsed.path, parse_qs(parsed.query)

        if path in PAGES:
            return self.serve_file(PAGES[path], "text/html; charset=utf-8")
        if path == "/api/frame.jpg":
            device_id = q.get("device", [None])[0] or q.get("node_id", [None])[0]
            return self.long_poll_frame(device_id, int(q.get("after", ["-1"])[0] or -1))
        if path == "/api/devices":
            now = time.time()
            dev_list = []
            for d_id, d in devices.items():
                is_online = (now - d["last_seen"] < FRAME_STALE_SEC) if d["last_seen"] else False
                dev_list.append({
                    "node_id": d["node_id"],
                    "name": d["name"],
                    "online": is_online,
                    "status": "ACTIVE" if is_online else "STANDBY",
                    "fps": d["fps"] if is_online else 0,
                    "battery": d["sensors"].get("battery_pct", 92),
                    "tilt": d["sensors"].get("tilt_deg", 5),
                    "ch4": d["sensors"].get("ch4_methane_ppm", 16),
                    "co": d["sensors"].get("co_ppm", 7),
                    "clearance": d["sensors"].get("void_clearance_m", 1.15),
                    "location": d["location"],
                    "coordinates": f"{d['lat']:.4f}° N, {d['lng']:.4f}° E",
                    "detection": d["detection"]
                })
            return self.send_json({"devices": dev_list, "active_device": active_device_id})
        if path == "/api/detections":
            return self.send_json(detection_events)
        if path == "/api/targets":
            return self.send_json(mission_targets)
        if path == "/api/telemetry/latest":
            dev = get_or_create_device(active_device_id)
            now = time.time()
            is_online = (now - dev["last_seen"] < FRAME_STALE_SEC) if dev["last_seen"] else False
            out = {
                "node_id": dev["node_id"],
                "name": dev["name"],
                "status": "ACTIVE" if is_online else "STANDBY",
                "rover_online": is_online,
                "sensors": dev["sensors"],
                "detection": dev["detection"],
                "fps": dev["fps"] if is_online else 0,
                "location": dev["location"]
            }
            return self.send_json(out)
        if path == "/stream.mjpg":
            return self.stream_mjpeg()
        if path == "/api/rover_cmd":
            cmd = q.get("cmd", ["stop"])[0]
            spd = q.get("spd", [q.get("speed", ["180"])])[0]
            ip = q.get("ip", ["192.168.4.1"])[0]
            global latest_rover_cmd
            latest_rover_cmd = {"cmd": cmd, "spd": spd, "ip": ip, "time": time.time()}
            if ip and ip not in ("none", "null", "undefined"):
                try:
                    import urllib.request
                    urllib.request.urlopen(f"http://{ip}/drive?cmd={cmd}&spd={spd}", timeout=0.35)
                except Exception:
                    pass
            return self.send_json({"status": "ok", "cmd": cmd, "spd": spd, "ip": ip})
        if path == "/api/ping":
            return self.send_json({"status": "ok", "time": time.time(), "ip": lan_ip(), "port": PORT_HTTPS, "devices_count": len(devices)})
        if path.startswith("/static/"):
            full = os.path.realpath(os.path.join(BASE_DIR, path[1:]))
            if full.startswith(os.path.join(BASE_DIR, "static")) and os.path.isfile(full):
                ctype = {".js": "application/javascript", ".json": "application/json",
                         ".css": "text/css"}.get(os.path.splitext(full)[1], "application/octet-stream")
                with open(full, "rb") as f:
                    return self._send(200, f.read(), ctype)
        self._send(404, b"Not found")

    def long_poll_frame(self, device_id, after):
        """Return the newest frame for target device as soon as seq != after (or 204 after 1 s)."""
        deadline = time.time() + 1.0
        target_id = (device_id or active_device_id or "MOTO-G62").upper()
        with frame_cond:
            dev = get_or_create_device(target_id)
            while dev["frame"]["seq"] == after or not dev["frame"]["jpg"] or (time.time() - dev["frame"]["t"] > FRAME_STALE_SEC):
                left = deadline - time.time()
                if left <= 0:
                    age = round(time.time() - dev["frame"]["t"], 2) if dev["frame"]["t"] else 999
                    return self._send(204, b"", extra={
                        "X-Seq": str(dev["frame"]["seq"]),
                        "X-Device": target_id,
                        "X-Age": str(age),
                        "X-Det": json.dumps(dev["detection"])})
                frame_cond.wait(left)
                dev = get_or_create_device(target_id)
            jpg, seq, t = dev["frame"]["jpg"], dev["frame"]["seq"], dev["frame"]["t"]
            det = dev["detection"]
        self._send(200, jpg, "image/jpeg", extra={
            "X-Seq": str(seq), "X-Device": target_id,
            "X-Age": str(round(time.time() - t, 2)),
            "X-Det": json.dumps(det)})

    def stream_mjpeg(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=sjframe")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        last = -1
        try:
            while True:
                with frame_cond:
                    while frame["seq"] == last or not frame["jpg"]:
                        frame_cond.wait(2.0)
                    jpg, last = frame["jpg"], frame["seq"]
                self.wfile.write(b"--sjframe\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg))
                self.wfile.write(jpg)
                self.wfile.write(b"\r\n")
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError, OSError):
            pass

    def do_POST(self):
        parsed = urlparse(self.path)
        path, q = parsed.path, parse_qs(parsed.query)
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length > MAX_FRAME_BYTES:
            self.close_connection = True
            return self._send(413, b"too large")
        body = self.rfile.read(length) if length > 0 else b""

        if path == "/api/frame":
            return self.handle_frame(body, q)
        if path == "/api/telemetry":
            return self.handle_telemetry(body)
        if path == "/api/active-device":
            global active_device_id
            try:
                data = json.loads(body.decode("utf-8") or "{}")
                if data.get("device"):
                    active_device_id = data["device"].upper()
            except Exception:
                pass
            return self.send_json({"active_device": active_device_id})
        if path == "/api/signoff":
            return self.handle_signoff(body)
        if path == "/api/rover_cmd":
            try:
                data = json.loads(body.decode("utf-8") or "{}")
                cmd = data.get("cmd", "stop")
                spd = str(data.get("spd", data.get("speed", 180)))
                ip = data.get("ip", "192.168.4.1")
                global latest_rover_cmd
                latest_rover_cmd = {"cmd": cmd, "spd": spd, "ip": ip, "time": time.time()}
                if ip and ip not in ("none", "null", "undefined"):
                    try:
                        import urllib.request
                        urllib.request.urlopen(f"http://{ip}/drive?cmd={cmd}&spd={spd}", timeout=0.35)
                    except Exception:
                        pass
                return self.send_json({"status": "ok", "cmd": cmd, "spd": spd, "ip": ip})
            except Exception as e:
                return self.send_json({"error": str(e)}, 400)
        if path == "/api/reset":
            detection_events.clear()
            return self.send_json({"status": "reset"})
        self.send_json({"error": "Endpoint not found"}, 404)

    def handle_frame(self, body, q):
        global active_device_id
        if not body.startswith(b"\xff\xd8"):
            return self.send_json({"error": "not a jpeg"}, 400)
        g = lambda k, d="": q.get(k, [d])[0]
        node_id = g("node_id", g("device", "MOTO-G62")).upper()
        dev = get_or_create_device(node_id)
        try:
            detected = g("d") == "1"
            conf = max(0.0, min(1.0, float(g("c", "0"))))
            box = [int(v) for v in g("b", "0,0,0,0").split(",")][:4]
        except ValueError:
            detected, conf, box = False, 0.0, [0, 0, 0, 0]
        det = {"detected": detected, "class": "HUMAN LIMB / SURVIVOR" if detected else "None",
               "confidence": round(conf, 2), "box": box}
        now = time.time()
        with frame_cond:
            dev["frame"]["jpg"] = body
            dev["frame"]["seq"] += 1
            dev["frame"]["t"] = now
            dev["last_seen"] = now
            dev["status"] = "ACTIVE"
            dev["detection"] = det
            frame["jpg"], frame["seq"], frame["t"] = body, dev["frame"]["seq"], now
            
            dev["fps_count"] += 1
            if now - dev["fps_t0"] >= 1.0:
                dev["fps"] = round(dev["fps_count"] / (now - dev["fps_t0"]), 1)
                dev["fps_count"] = 0
                dev["fps_t0"] = now
                
            if detected and conf >= 0.35:
                if now - dev.get("last_alert_time", 0) > 4.0:
                    dev["last_alert_time"] = now
                    add_detection_event(node_id, dev["name"], dev["location"], dev["lat"], dev["lng"], round(conf * 100))
                    
            frame_cond.notify_all()
        self.send_json({"ok": True, "seq": dev["frame"]["seq"], "device": node_id})

    def handle_telemetry(self, body):
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            data = {}
        node_id = data.get("node_id", "MOTO-G62").upper()
        dev = get_or_create_device(node_id)
        with state_lock:
            dev["last_seen"] = time.time()
            if isinstance(data.get("sensors"), dict):
                dev["sensors"].update(data["sensors"])
            if data.get("location"):
                dev["location"] = data["location"]
        self.send_json({"status": "received", "ack": True, "device": node_id})

    def handle_signoff(self, body):
        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except Exception:
            data = {}
        incident_id = data.get("incident_id", "INC-101")
        commander = data.get("commander", "Commander Nishant Pathak (Team Aprajit)")
        action = data.get("action", "DISPATCH_USAR_SQUAD")
        payload = f"{incident_id}:{commander}:{action}:{time.time()}"
        signoff_hash = hashlib.sha256(payload.encode()).hexdigest()
        with state_lock:
            for inc in incidents_db:
                if inc["id"] == incident_id:
                    inc["status"] = f"APPROVED BY COMMANDER ({action})"
                    inc["signoff_hash"] = signoff_hash
                    break
        try:
            conn = sqlite3.connect(DB_FILE, timeout=2)
            conn.execute("INSERT INTO audit_log (timestamp,incident_id,commander,action,signoff_hash) VALUES (?,?,?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), incident_id, commander, action, signoff_hash))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Audit log error:", e)
        self.send_json({"status": "APPROVED", "signoff_hash": signoff_hash, "insarag_compliant": True,
                        "timestamp": datetime.now().strftime("%H:%M:%S")})


# ---------------------------------------------------------------- servers
class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    request_queue_size = 32
    allow_reuse_address = True
    ssl_ctx = None

    def process_request_thread(self, request, client_address):
        # TLS handshake happens HERE (worker thread), never on the accept loop.
        try:
            if self.ssl_ctx is not None:
                request.settimeout(10)
                request = self.ssl_ctx.wrap_socket(request, server_side=True)
            self.finish_request(request, client_address)
        except (ssl.SSLError, ConnectionError, socket.timeout, OSError):
            pass  # phone dropped / cert prompt abandoned: harmless
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def handle_error(self, request, client_address):
        pass


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_servers():
    init_db()
    ip = lan_ip()
    print("=====================================================")
    print("  SANJEEVNI FIELD TACTICAL GATEWAY")
    print("=====================================================")
    print(f"  War Room (laptop):  http://localhost:{PORT_HTTP}/")
    print(f"  Rover (phone):      https://{ip}:{PORT_HTTPS}/rover")
    print(f"  3D Simulator:       http://{ip}:{PORT_HTTP}/3d-simulation")
    print(f"  Routing Map:        http://{ip}:{PORT_HTTP}/routing-map")
    print("=====================================================", flush=True)

    http_srv = ThreadingServer(("", PORT_HTTP), SanjeevniHandler)
    threading.Thread(target=http_srv.serve_forever, daemon=True).start()

    https_srv = ThreadingServer(("", PORT_HTTPS), SanjeevniHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    https_srv.ssl_ctx = ctx
    try:
        https_srv.serve_forever()
    except KeyboardInterrupt:
        print("\nGateway shut down.")


if __name__ == "__main__":
    run_servers()
