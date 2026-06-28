"""
domain_weights.py
=================
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
Document: TC-ENG-DOM-001

Domain-Specific CCI Weight Tables
-----------------------------------
The CCI is a weighted composite of five diagnostic channels. Optimal
weights differ by domain because the physical precursor mechanisms differ:

  SEISMIC   — Stress accumulation on fault planes. b-value decay is the
               dominant published precursor. Phase coupling (PLV) reflects
               inter-fault synchronisation. Attractor drift captures
               nonlinear slip instability.

  VOLCANIC  — Harmonic tremor and fluid resonance dominate. Spectral
               coherence and PLV (mode-locking of fluid resonance) carry
               more weight than magnitude statistics, which are sparse
               in volcanic swarms.

  STRUCTURAL — Acoustic emission burst clustering and phase-space
               geometry dominate. b-value is retained but down-weighted;
               structural AE catalogues are too small for reliable
               Gutenberg-Richter fits at short windows.

IMPORTANT: These weights are physically motivated starting estimates.
They are NOT empirically optimised. Weight optimisation against real
instrument data (IRIS/FDSN seismic, VAAC volcanic, AE structural) is
the next validation milestone. Do NOT represent these as tuned weights
in any buyer communication until that optimisation is complete.

Trade secret: all weight values and thresholds are proprietary to
AW IP Holdings Inc. and are never exposed in API responses.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Final, Mapping

# ── Type alias ────────────────────────────────────────────────────────────────

WeightMap = Mapping[str, float]

# ── Alert thresholds (shared across all domains) ──────────────────────────────
# Escalation requires both CCI threshold AND persistence gate.
# Internal calibrated thresholds.

THRESHOLD_ADVISORY: Final[float] = 0.65
THRESHOLD_WARNING:  Final[float] = 0.78
THRESHOLD_CRITICAL: Final[float] = 0.88

# ── Persistence gate config ───────────────────────────────────────────────────
# Multi-window persistence prevents single-spike false alarms.
# Rule: alert level is only confirmed if enough recent CCI windows exceed the threshold.

PERSISTENCE_GATE: Final[Dict[str, Dict[str, int]]] = {
    "ADVISORY":  {"window": 5, "required": 2},   # 2 of last 5
    "WARNING":   {"window": 5, "required": 3},   # 3 of last 5
    "CRITICAL":  {"window": 8, "required": 5},   # 5 of last 8
}

# ── Surrogate rejection gate ──────────────────────────────────────────────────
# Real CCI must exceed surrogate mean by this many sigma to confirm alert.
SURROGATE_Z_MIN: Final[Dict[str, float]] = {
    "ADVISORY":  1.5,
    "WARNING":   2.0,
    "CRITICAL":  2.5,
}

# ── Confidence floor by alert level ──────────────────────────────────────────
CONFIDENCE_FLOOR: Final[Dict[str, float]] = {
    "NOMINAL":   0.0,
    "ADVISORY":  0.50,
    "WARNING":   0.65,
    "CRITICAL":  0.80,
}

# ── Domain weight tables ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainConfig:
    """
    Immutable domain configuration.

    frozen=True prevents accidental field reassignment after construction.
    weights is wrapped in MappingProxyType so dict contents are also
    read-only — callers cannot mutate global configuration at runtime.
    """
    name:        str
    description: str
    weights:     WeightMap

    def __post_init__(self) -> None:
        # Wrap weights in MappingProxyType at construction time.
        # frozen=True blocks direct field reassignment; MappingProxyType
        # blocks mutation of the dict contents themselves.
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))
        total = sum(self.weights.values())
        if abs(total - 1.0) >= 1e-6:
            raise ValueError(
                f"Domain '{self.name}' weights sum to {total:.6f}, must sum to 1.0"
            )


DOMAIN_CONFIGS: Final[Dict[str, DomainConfig]] = {

    "seismic": DomainConfig(
        name="seismic",
        description=(
            "Tectonic / induced seismicity. b-value decay is the dominant "
            "published precursor. PLV captures inter-fault synchronisation. "
            "Attractor drift detects nonlinear slip geometry changes."
        ),
        weights={
            "b_value":         0.28,
            "kappa":           0.18,
            "attractor_drift": 0.24,
            "plv":             0.18,
            "ljung_box":       0.12,
        },
    ),

    "volcanic": DomainConfig(
        name="volcanic",
        description=(
            "Volcanic tremor and fluid resonance. Harmonic mode-locking (PLV) "
            "and spectral geometry dominate. b-value is down-weighted due to "
            "sparse volcanic seismicity catalogues at short windows."
        ),
        weights={
            "b_value":         0.12,
            "kappa":           0.18,
            "attractor_drift": 0.26,
            "plv":             0.28,
            "ljung_box":       0.16,
        },
    ),

    "structural": DomainConfig(
        name="structural",
        description=(
            "Structural acoustic emission. Phase-space geometry and temporal "
            "clustering dominate. b-value retained but down-weighted — AE "
            "catalogues are too small for reliable G-R fits at short windows."
        ),
        weights={
            "b_value":         0.10,
            "kappa":           0.18,
            "attractor_drift": 0.30,
            "plv":             0.24,
            "ljung_box":       0.18,
        },
    ),
}

# ── Accessors ─────────────────────────────────────────────────────────────────

def get_domain_config(domain: str) -> DomainConfig:
    """
    Return DomainConfig for the named domain.
    Raises ValueError for unknown domains.
    Callers receive the frozen config object directly — weights are
    read-only via MappingProxyType and fields cannot be reassigned.
    """
    key = domain.lower().strip()
    if key not in DOMAIN_CONFIGS:
        raise ValueError(
            f"Unknown domain '{domain}'. "
            f"Valid domains: {sorted(DOMAIN_CONFIGS.keys())}"
        )
    return DOMAIN_CONFIGS[key]


def list_domains() -> dict[str, str]:
    """Return {domain_name: short_description} — safe for API exposure."""
    return {
        "seismic":    "Seismic waveform precursor analysis.",
        "volcanic":   "Volcanic tremor precursor analysis.",
        "structural": "Structural acoustic emission precursor analysis.",
    }
