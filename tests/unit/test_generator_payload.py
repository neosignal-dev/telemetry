import importlib.util
import pathlib


def load_generator_module():
    root = pathlib.Path(__file__).resolve().parents[3]
    module_path = root / "services" / "telemetry-generator" / "main.py"
    spec = importlib.util.spec_from_file_location("telemetry_generator", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def test_generate_payload_shape():
    gen = load_generator_module()
    payload = gen.generate_payload("SAT-001", "EU")

    assert isinstance(payload, dict)
    assert payload["sat_id"] == "SAT-001"
    assert payload["orbit"] == gen.ORBIT
    assert payload["region"] == "EU"
    assert "ts" in payload and isinstance(payload["ts"], str)
    assert isinstance(payload["battery"], (int, float))

    link = payload["link"]
    assert {"uplink_mbps", "downlink_mbps", "latency_ms", "packet_loss_pct"}.issubset(link.keys())
    assert all(isinstance(link[k], (int, float)) for k in link)

