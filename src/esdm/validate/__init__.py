"""Process-specific and held-out validation primitives."""

from .ladder import *
from . import known_truth as _known_truth
from .known_truth import KnownTruthWorld, make_v03_known_truth_worlds
from .sbc_gate import V03SBCGateConfig, V03SBCGateDecision, evaluate_v03_sbc_gate
from .v031_sbc_gate import (
    V031GateCheck,
    V031SBCGateConfig,
    V031SBCGateDecision,
    evaluate_v031_sbc_gate,
)

# Transitional compatibility: the retired validation API was first specified under
# esdm.validate.known_truth. Keep that historical import path working without mixing it
# with the distinct v0.3.1 gate.
_known_truth.V03SBCGateConfig = V03SBCGateConfig
_known_truth.V03SBCGateDecision = V03SBCGateDecision
_known_truth.evaluate_v03_sbc_gate = evaluate_v03_sbc_gate

__all__ = [name for name in globals() if not name.startswith("_")]
