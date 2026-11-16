"""Simulated vCenter / ESXi REST API (no VMware needed).
  POST /api/session (Basic auth)  -> session token (JSON string)
  GET  /api/vcenter/host, /api/vcenter/vm, /api/sensors
Fault injection: POST /sim/<start_vm|stop_vm|cpu_load|psu_red|reset>
"""
import random, base64
from flask import Flask, request, jsonify

app = Flask(__name__)
TOKEN = "vmware-api-session-id-demo"
S = {"vm_started": False, "cpu_load": False, "psu_red": False}

def authed():
    return request.headers.get("vmware-api-session-id") == TOKEN

@app.post("/api/session")
def session():
    h = request.headers.get("Authorization", "")
    try:
        user, pw = base64.b64decode(h.split()[1]).decode().split(":", 1)
    except Exception:
        return jsonify(error="unauthenticated"), 401
    if (user, pw) != ("administrator@vsphere.local", "admin"):
        return jsonify(error="unauthenticated"), 401
    return jsonify(TOKEN)

@app.get("/api/vcenter/host")
def hosts():
    if not authed(): return jsonify(error="unauthenticated"), 401
    cpu = 6200 if S["cpu_load"] or S["vm_started"] else 600
    cpu += random.randint(-40, 40)
    return jsonify([{"host": "host-10", "name": "10.10.51.15", "connection_state": "CONNECTED",
                     "power_state": "POWERED_ON", "cpu_used_mhz": cpu,
                     "memory_used_mb": 14200 + (4096 if S["vm_started"] else 0) + random.randint(-30, 30)}])

@app.get("/api/vcenter/vm")
def vms():
    if not authed(): return jsonify(error="unauthenticated"), 401
    v = [{"vm": "vm-1", "name": "web-01", "power_state": "POWERED_ON"},
         {"vm": "vm-2", "name": "db-01", "power_state": "POWERED_ON"},
         {"vm": "vm-3", "name": "ubuntu-test", "power_state": "POWERED_ON" if S["vm_started"] else "POWERED_OFF"}]
    return jsonify(v)

@app.get("/api/sensors")
def sensors():
    if not authed(): return jsonify(error="unauthenticated"), 401
    return jsonify([
        {"name": "Power Supply 1", "state": "green"},
        {"name": "Power Supply 2", "state": "red" if S["psu_red"] else "green"},
        {"name": "Fan Device 1", "state": "green"},
        {"name": "Storage 1", "state": "green"}])

@app.post("/sim/<what>")
def sim(what):
    if what == "reset":
        for k in S: S[k] = False
    elif what == "start_vm": S["vm_started"] = True
    elif what == "stop_vm": S["vm_started"] = False
    elif what in S: S[what] = True
    else: return jsonify(error="unknown"), 404
    return jsonify(S)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
