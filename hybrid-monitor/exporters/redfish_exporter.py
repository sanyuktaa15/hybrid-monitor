"""RedFishExporter: Redfish -> Prometheus (port 9141). Mirrors the paper's agent:
GetSession, CreateRequest, GetPower, GetThermal, Logout (X-Auth-Token).
Health encoding: 1 = OK, 0 = anything else."""
import os, requests
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY
import time

BASE = os.environ.get("REDFISH_URL", "http://redfish-mock:8001")
USER, PWD = os.environ.get("REDFISH_USER", "admin"), os.environ.get("REDFISH_PASS", "admin")
HOST = os.environ.get("REDFISH_HOST", "ilo-demo-01")

class Client:
    def get_session(self):
        r = requests.post(f"{BASE}/redfish/v1/SessionService/Sessions",
                          json={"UserName": USER, "Password": PWD}, timeout=4)
        r.raise_for_status()
        self.tok, self.loc = r.headers["X-Auth-Token"], r.headers["Location"]
    def create_request(self, path):
        r = requests.get(BASE + path, headers={"X-Auth-Token": self.tok}, timeout=4)
        r.raise_for_status(); return r.json()
    def get_power(self):   return self.create_request("/redfish/v1/Chassis/1/Power")
    def get_thermal(self): return self.create_request("/redfish/v1/Chassis/1/Thermal")
    def logout(self):
        requests.delete(BASE + self.loc, headers={"X-Auth-Token": self.tok}, timeout=4)

ok = lambda s: 1 if (s or {}).get("Health") == "OK" else 0

class Collector:
    def collect(self):
        t0 = time.time()
        up = GaugeMetricFamily("redfish_exporter_up", "Redfish endpoint reachable", labels=["host"])
        try:
            c = Client(); c.get_session()
            th, pw = c.get_thermal(), c.get_power(); c.logout()
        except Exception as e:
            up.add_metric([HOST], 0); yield up; return
        up.add_metric([HOST], 1); yield up
        sh = GaugeMetricFamily("redfish_exporter_SensorHealth", "1=OK 0=not OK", labels=["host", "sensor"])
        st = GaugeMetricFamily("redfish_exporter_SensorTemp", "Temperature (C)", labels=["host", "sensor"])
        fs = GaugeMetricFamily("redfish_exporter_FanStatus", "1=OK 0=failed", labels=["host", "fan"])
        fr = GaugeMetricFamily("redfish_exporter_FanSpeed", "Fan speed (%)", labels=["host", "fan"])
        pc = GaugeMetricFamily("redfish_exporter_PowerWatts", "Power consumed (W)", labels=["host"])
        for t in th["Temperatures"]:
            sh.add_metric([HOST, t["Name"]], ok(t["Status"])); st.add_metric([HOST, t["Name"]], t["ReadingCelsius"])
        for f in th["Fans"]:
            fs.add_metric([HOST, f["Name"]], ok(f["Status"])); fr.add_metric([HOST, f["Name"]], f["Reading"])
        for p in pw["PowerSupplies"]:
            sh.add_metric([HOST, p["Name"]], ok(p["Status"]))
        pc.add_metric([HOST], pw["PowerControl"][0]["PowerConsumedWatts"])
        d = GaugeMetricFamily("redfish_exporter_scrape_seconds", "Time to query Redfish", labels=["host"])
        d.add_metric([HOST], time.time() - t0)
        yield from (sh, st, fs, fr, pc, d)

if __name__ == "__main__":
    REGISTRY.register(Collector())
    start_http_server(9141)
    print("RedFishExporter on :9141", flush=True)
    while True: time.sleep(3600)
