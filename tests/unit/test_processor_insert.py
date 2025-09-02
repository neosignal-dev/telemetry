import importlib.util
import json
import pathlib


def load_processor_module():
    root = pathlib.Path(__file__).resolve().parents[3]
    module_path = root / "services" / "telemetry-processor" / "main.py"
    spec = importlib.util.spec_from_file_location("telemetry_processor", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def test_processor_metrics_exports_exist():
    proc = load_processor_module()
    # Exists and are Counter/Histogram types
    assert hasattr(proc, "ingested_total")
    assert hasattr(proc, "ingested_by_sat_total")
    assert hasattr(proc, "processing_latency_s")
    assert hasattr(proc, "db_errors_total")

    # sample labels update should not raise
    proc.ingested_by_sat_total.labels(sat_id="SAT-001", region="EU").inc()

