# Hybrid Server Monitoring: Redfish + vSphere + Prometheus (runs entirely on a laptop)

Reproduces the framework of Dakic et al., "The RedFish API and vSphere Hypervisor API: A Unified
Framework for Policy-Based Server Monitoring", Electronics 2024, 13(23), 4624.
No server, BMC or VMware needed: both interfaces are simulated.

## Run
Install Docker Desktop, then in this folder:

    docker compose up --build

| What | URL | Login |
|---|---|---|
| Grafana dashboard | http://localhost:3000 | admin / admin |
| Prometheus (targets, alerts) | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| Received e-mails (MailHog) | http://localhost:8025 | - |
| Redfish exporter metrics | http://localhost:9141/metrics | - |
| vSphere exporter metrics | http://localhost:9142/metrics | - |

## Demo (inject faults, watch alerts)
    ./demo.sh fan     # Fan 2 fails       -> fan_down fires after 1 min
    ./demo.sh vm      # VM starts, CPU up -> cpu_increase_load after 30 s
    ./demo.sh psu     # PSU fails in both -> sensor_down and hybrid_power_supply
    ./demo.sh temp    # CPU 1 overheats   -> sensor_down
    ./demo.sh reset   # back to normal
Alerts appear in Prometheus > Alerts and as e-mails in MailHog. On Windows run the curl lines from demo.sh in PowerShell/Git Bash.
Stop an exporter (`docker compose stop redfish-exporter`) to see service_down after 2 min.

## Architecture
mock Redfish / mock vSphere -> RedFishExporter (:9141) / VsphereExporter (:9142)
-> Prometheus (10 s global, 5 s jobs) -> Alertmanager -> e-mail ; Grafana reads Prometheus.
Versions follow the paper: Prometheus 2.40.0, Alertmanager 0.24.0, Grafana 9.2.4.

## Differences from the paper (state these in your report)
- Simulated endpoints instead of HPE iLO and a real vSphere 7.0u3 host.
- Exporters in Python, not Go; no Vue.js/Go management web interface or PostgreSQL.
- The CPU and hybrid power rules are Prometheus rules here (Grafana-managed in the paper).
- CPU threshold is 2000 MHz here (200 MHz in the paper) to suit the simulated host.
- Metric names follow the paper's style (redfish_exporter_SensorHealth etc.), values are simulated.
