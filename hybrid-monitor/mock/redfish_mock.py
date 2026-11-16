"""Simulated HPE-iLO-style Redfish service (no hardware needed).
Implements only what the RedFish agent of the paper uses:
  POST /redfish/v1/SessionService/Sessions   -> X-Auth-Token
  GET  /redfish/v1/Chassis/1/Thermal
  GET  /redfish/v1/Chassis/1/Power
  DELETE /redfish/v1/SessionService/Sessions/<id>   (logout)
Fault injection:  POST /sim/<fan_fail|temp_spike|psu_fail|reset>
"""
import random, uuid
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
SESSIONS = set()
S = {"fan_fail": False, "temp_spike": False, "psu_fail": False}

def authed():
    return request.headers.get("X-Auth-Token") in SESSIONS

@app.post("/redfish/v1/SessionService/Sessions")
def login():
    b = request.get_json(silent=True) or {}
    if b.get("UserName") != "admin" or b.get("Password") != "admin":
        return jsonify(error="bad credentials"), 401
    tok = uuid.uuid4().hex
    SESSIONS.add(tok)
    r = make_response(jsonify({"Id": tok[:8], "UserName": "admin"}), 201)
    r.headers["X-Auth-Token"] = tok
    r.headers["Location"] = f"/redfish/v1/SessionService/Sessions/{tok[:8]}"
    return r

@app.delete("/redfish/v1/SessionService/Sessions/<sid>")
def logout(sid):
    for t in list(SESSIONS):
        if t.startswith(sid):
            SESSIONS.discard(t)
    return "", 204

def health(ok):
    return {"State": "Enabled", "Health": "OK" if ok else "Critical"}

@app.get("/redfish/v1/Chassis/1/Thermal")
def thermal():
    if not authed():
        return jsonify(error="no session"), 401
    j = lambda: random.uniform(-0.6, 0.6)
    cpu = 92 + j() if S["temp_spike"] else 42 + j()
    temps = [
        {"Name": "CPU 1", "ReadingCelsius": round(cpu, 1), "UpperThresholdCritical": 85,
         "UpperThresholdFatal": 100, "Status": health(cpu < 85)},
        {"Name": "CPU 2", "ReadingCelsius": round(40 + j(), 1), "UpperThresholdCritical": 85,
         "UpperThresholdFatal": 100, "Status": health(True)},
        {"Name": "Inlet Ambient", "ReadingCelsius": round(24 + j(), 1),
         "UpperThresholdCritical": 42, "UpperThresholdFatal": 47, "Status": health(True)},
    ]
    fans = []
    for i in range(1, 5):
        bad = S["fan_fail"] and i == 2
        fans.append({"Name": f"Fan {i}", "Reading": 0 if bad else round(38 + 2 * j()),
                     "ReadingUnits": "Percent", "Status": health(not bad)})
    return jsonify({"Temperatures": temps, "Fans": fans})

@app.get("/redfish/v1/Chassis/1/Power")
def power():
    if not authed():
        return jsonify(error="no session"), 401
    psus = [{"Name": "PSU 1", "Status": health(True)},
            {"Name": "PSU 2", "Status": health(not S["psu_fail"])}]
    return jsonify({"PowerControl": [{"PowerConsumedWatts": round(310 + 12 * random.uniform(-1, 1))}],
                    "PowerSupplies": psus})

@app.post("/sim/<what>")
def sim(what):
    if what == "reset":
        for k in S: S[k] = False
    elif what in S:
        S[what] = True
    else:
        return jsonify(error="unknown"), 404
    return jsonify(S)

@app.get("/sim")
def state():
    return jsonify(S)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
