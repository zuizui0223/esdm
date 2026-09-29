import importlib.util
from pathlib import Path
import sys


def _load(name, filename):
    path = Path(__file__).resolve().parents[1] / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tr1_scripts_pin_frozen_contract_blob():
    replicate = _load("tr1_replicate", "run_tr1_replicate.py")
    aggregate = _load("tr1_aggregate", "aggregate_tr1.py")

    expected = "91114caab4713ae48ac2976a56935abfdbbf51a2"
    assert replicate.FROZEN_CONTRACT_BLOB_SHA == expected
    assert aggregate.FROZEN_CONTRACT_BLOB_SHA == expected
