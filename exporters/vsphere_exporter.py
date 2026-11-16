"""VsphereExporter: vSphere REST API -> Prometheus (port 9142).
Status encoding as in the paper: 2 = OK, 1 = warning, 0 = critical."""
import os, requests, time
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

BASE = os.environ.get("VSPHERE_URL", "http://vsphere-mock:8002")
USER, PWD = os.environ.get("VSPHERE_USER", "administrator@vsphere.local"), os.environ.get("VSPHERE_PASS", "admin")

class Collector:
    def collect(self):
        up = GaugeMetricFamily("vsphere_exporter_up", "vCenter reachable", labels=["host"])
        try:
            tok = requests.post(f"{BASE}/api/session", auth=(USER, PWD), timeout=4).json()
            h = {"vmware-api-session-id": tok}
            hosts = requests.get(f"{BASE}/api/vcenter/host", headers=h, timeout=4).json()
            vms = requests.get(f"{BASE}/api/vcenter/vm", headers=h, timeout=4).json()
            sens = requests.get(f"{BASE}/api/sensors", headers=h, timeout=4).json()
        except Exception:
            up.add_metric(["vcenter"], 0); yield up; return
        up.add_metric(["vcenter"], 1); yield up
        cpu = GaugeMetricFamily("vsphere_exporter_CpuMhz", "Host CPU used (MHz)", labels=["host"])
        mem = GaugeMetricFamily("vsphere_exporter_MemMB", "Host memory used (MB)", labels=["host"])
        hs = GaugeMetricFamily("vsphere_exporter_HostState", "1=connected", labels=["host"])
        for x in hosts:
            cpu.add_metric([x["name"]], x["cpu_used_mhz"]); mem.add_metric([x["name"]], x["memory_used_mb"])
            hs.add_metric([x["name"]], 1 if x["connection_state"] == "CONNECTED" else 0)
        vm = GaugeMetricFamily("vsphere_exporter_VmPowerState", "1=powered on", labels=["vm"])
        for v in vms: vm.add_metric([v["name"]], 1 if v["power_state"] == "POWERED_ON" else 0)
        si = GaugeMetricFamily("vsphere_exporter_SensorInfo", "2=green 1=yellow 0=red", labels=["host", "name", "state"])
        code = {"green": 2, "yellow": 1, "red": 0}
        for s in sens: si.add_metric([hosts[0]["name"], s["name"], s["state"]], code[s["state"]])
        yield from (cpu, mem, hs, vm, si)

if __name__ == "__main__":
    REGISTRY.register(Collector())
    start_http_server(9142)
    print("VsphereExporter on :9142", flush=True)
    while True: time.sleep(3600)
