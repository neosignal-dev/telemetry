import os
import time
import json
import urllib.request


def http_get(url: str, timeout: float = 5.0) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as r:  # nosec B310
        return r.read().decode()


def http_post_json(url: str, payload: dict, timeout: float = 5.0) -> str:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
        return r.read().decode()


def test_stack_smoke_when_running_locally():
    # Assume compose stack is already up
    # 1) Hit collector
    http_post_json("http://localhost:8080/ingest", {"sat_id": "SAT-999", "region": "EU", "battery": 80, "link": {"uplink_mbps": 10, "downlink_mbps": 50, "latency_ms": 40, "packet_loss_pct": 0.2}})

    # 2) Poll Prometheus for increase in counters
    t0 = time.time()
    increased = False
    while time.time() - t0 < 20:
        try:
            body = http_get("http://localhost:9090/api/v1/query?query=sum(rate(telemetry_ingested_total[1m]))")
            if "result" in body and "data" in body:
                # very light check, we just ensure API is reachable
                increased = True
                break
        except Exception:
            pass
        time.sleep(1)
    assert increased, "Prometheus query did not succeed in time"

    # 3) Grafana health
    health = http_get("http://localhost:3000/api/health")
    assert "commit" in health

