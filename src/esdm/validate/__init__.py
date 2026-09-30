"""Process-specific and held-out validation primitives."""

from .ladder import *
from . import known_truth as _known_truth
from .known_truth import KnownTruthWorld, make_v03_known_truth_worlds
from .field1_gate import (
    Field1ComparisonSummary,
    Field1GateCheck,
    Field1GateConfig,
    Field1GateDecision,
    evaluate_field1_gate,
    summarize_field1_gains,
)
from .field1_run import (
    FROZEN_FIELD1_MCMC_PROFILE,
    Field1MCMCProfile,
    Field1ReplicateResult,
    field1_required_fit_plan,
    run_field1_replicate,
)
from .field1_known_truth import (
    Field1Fixture,
    Field1KnownTruthWorld,
    barrier_transfer_geometry_audit,
    field1_truth_theta,
    make_field1_fixture,
    make_field1_mean_covariance_factorial,
    make_field1_model,
    make_field1_primary_worlds,
    matched_barrier_distance_strata,
    subset_presence_data,
    training_edge_axis_rank_audit,
)
from .sbc_gate import V03SBCGateConfig, V03SBCGateDecision, evaluate_v03_sbc_gate
from .e5_candidate import qualify_e5_candidate_metadata
from .amap1_known_truth import (
    AMap1Fixture,
    AMap1World,
    make_amap1_fixtures,
    make_amap1_model,
    make_amap1_worlds,
)
from .amap1_gate import (
    AMap1GateConfig,
    AMap1GateDecision,
    AMap1WorldSummary,
    evaluate_amap1_gate,
    summarize_amap1_world,
)
from .amap1_run import (
    AMap1MCMCProfile,
    AMap1ReplicateResult,
    FROZEN_AMAP1_MCMC_PROFILE,
    amap1_required_fit_plan,
    run_amap1_replicate,
)
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
