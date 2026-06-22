"""
TC Domain Configuration
=======================
AW IP Holdings Inc. | CONFIDENTIAL

Per-domain validation profiles and channel tuning hooks.

Current state: all three domains share the base CCI weights from the engine
(b_value 0.30 / kappa 0.25 / k_ratio 0.25 / ljung_box 0.20).

Per-domain weight overrides are documented below and will be activated
after IRIS/field validation data justifies the tuning:

  SEISMIC:     LB weight ↑ (foreshock clustering is primary precursor)
               b_value weight ↑ (G-R b-drop is well-established precursor)
               Candidate: b_value 0.35 / kappa 0.25 / k_ratio 0.20 / ljung_box 0.20

  VOLCANIC:    k_ratio weight ↑ (spectral shift from long-period tremor dominates)
               kappa weight ↑ (stress anisotropy precedes conduit pressurisation)
               Candidate: b_value 0.20 / kappa 0.30 / k_ratio 0.30 / ljung_box 0.20

  STRUCTURAL:  ljung_box weight ↑ (AE burst clustering is primary precursor)
               kappa weight ↑ (progressive shear-plane loading)
               Candidate: b_value 0.20 / kappa 0.30 / k_ratio 0.20 / ljung_box 0.30

These overrides require independent validation data before deployment.
Do not activate without corresponding IRIS-PASS or field-data results.
"""
from __future__ import annotations
from typing import Dict, List

# ── DOMAIN IDENTIFIERS ────────────────────────────────────────────────────────

DOMAINS = ("seismic", "volcanic", "structural")

# ── SHARED BASE WEIGHTS (active) ──────────────────────────────────────────────
# Matches tc_engine_v2._CCI_WEIGHTS exactly.
# Override per domain once validation data supports it.

BASE_WEIGHTS: Dict[str, float] = {
    "b_value":   0.30,
    "kappa":     0.25,
    "k_ratio":   0.25,
    "ljung_box": 0.20,
}

# ── PER-DOMAIN WEIGHT OVERRIDES (inactive — documented for future tuning) ─────
# Set active=True only after corresponding IRIS-PASS validation is attached.

DOMAIN_WEIGHT_OVERRIDES: Dict[str, Dict] = {
    "seismic": {
        "active": False,
        "weights": {"b_value": 0.35, "kappa": 0.25, "k_ratio": 0.20, "ljung_box": 0.20},
        "rationale": "G-R b-drop and foreshock clustering are primary seismic precursors.",
        "activation_condition": "IRIS-PASS on Tōhoku + Maule + Sumatra with these weights.",
    },
    "volcanic": {
        "active": False,
        "weights": {"b_value": 0.20, "kappa": 0.30, "k_ratio": 0.30, "ljung_box": 0.20},
        "rationale": "Long-period tremor spectral shift and conduit stress anisotropy dominate.",
        "activation_condition": "IRIS-PASS on Eyjafjallajökull + Pinatubo with these weights.",
    },
    "structural": {
        "active": False,
        "weights": {"b_value": 0.20, "kappa": 0.30, "k_ratio": 0.20, "ljung_box": 0.30},
        "rationale": "AE burst clustering and progressive shear-plane loading dominate.",
        "activation_condition": "Field-data PASS on at least two structural collapse AE datasets.",
    },
}


def get_weights(domain: str) -> Dict[str, float]:
    """
    Return active CCI weights for a domain.
    Falls back to BASE_WEIGHTS unless domain override is active.
    """
    override = DOMAIN_WEIGHT_OVERRIDES.get(domain, {})
    if override.get("active", False):
        return override["weights"]
    return BASE_WEIGHTS


# ── VALIDATION EVENT PROFILES ─────────────────────────────────────────────────

VALIDATION_PROFILES: Dict[str, List[Dict]] = {

    "seismic": [
        {
            "event_id":       "Tohoku_2011",
            "description":    "Mw 9.1 megathrust — offshore Honshu, Japan",
            "iris_station":   "IU.MAJO.00.BHZ",
            "onset_frac":     0.12,
            "severity_scale": 0.89,
            "seed":           2011,
            "source_ref":     "Nanjo et al. (2012), Earth Planets Space",
        },
        {
            "event_id":       "Maule_2010",
            "description":    "Mw 8.8 megathrust — Bio-Bio, Chile",
            "iris_station":   "IU.LVC.00.BHZ",
            "onset_frac":     0.15,
            "severity_scale": 0.84,
            "seed":           2010,
            "source_ref":     "Riquelme et al. (2010), Geophysical Research Letters",
        },
        {
            "event_id":       "Sumatra_2004",
            "description":    "Mw 9.1 megathrust — Sumatra-Andaman",
            "iris_station":   "II.KAPI.00.BHZ",
            "onset_frac":     0.10,
            "severity_scale": 0.91,
            "seed":           2004,
            "source_ref":     "Lay et al. (2005), Science",
        },
        {
            "event_id":       "NegativeControl_2007",
            "description":    "Quiescent 90-day window — no Mw>7 events",
            "iris_station":   "IU.MAJO.00.BHZ",
            "onset_frac":     None,          # no precursor onset — should not trigger
            "severity_scale": 0.0,
            "seed":           2007,
            "source_ref":     "IRIS/FDSN archive — quiet period",
            "is_negative_control": True,
        },
    ],

    "volcanic": [
        {
            "event_id":       "Eyjafjallajokull_2010",
            "description":    "VEI 4 sub-glacial eruption — Iceland",
            "iris_station":   "IU.BORG.00.BHZ",
            "onset_frac":     0.18,
            "severity_scale": 0.81,
            "seed":           2010,
            "source_ref":     "Sigmundsson et al. (2010), Nature",
        },
        {
            "event_id":       "Pinatubo_1991",
            "description":    "VEI 6 Plinian eruption — Luzon, Philippines",
            "iris_station":   "IU.GUMO.00.BHZ",
            "onset_frac":     0.18,
            "severity_scale": 0.87,
            "seed":           1991,
            "source_ref":     "Harlow et al. (1996), Fire and Mud, PHIVOLCS/USGS",
        },
        {
            "event_id":       "NegativeControl_Volcanic",
            "description":    "Quiescent volcanic arc period — no eruptions",
            "iris_station":   "IU.BORG.00.BHZ",
            "onset_frac":     None,
            "severity_scale": 0.0,
            "seed":           2008,
            "source_ref":     "IRIS/FDSN archive — quiet period",
            "is_negative_control": True,
        },
    ],

    "structural": [
        {
            "event_id":       "Rana_Plaza_2013",
            "description":    "Progressive collapse — 8-storey commercial building, Dhaka",
            "iris_station":   None,           # AE sensor data — not IRIS/FDSN
            "onset_frac":     0.22,
            "severity_scale": 0.76,
            "seed":           2013,
            "source_ref":     "Grosse & Ohtsu (2008), Acoustic Emission Testing; ACI 318-14",
        },
        {
            "event_id":       "GenericBridge_AE",
            "description":    "Synthetic fatigue-crack AE profile — steel bridge analogue",
            "iris_station":   None,
            "onset_frac":     0.25,
            "severity_scale": 0.72,
            "seed":           3001,
            "source_ref":     "Mistras Group AE benchmark datasets (structure class)",
        },
        {
            "event_id":       "NegativeControl_Structural",
            "description":    "Healthy structure AE baseline — no progressive loading",
            "iris_station":   None,
            "onset_frac":     None,
            "severity_scale": 0.0,
            "seed":           9999,
            "source_ref":     "Synthetic baseline — no precursor structure",
            "is_negative_control": True,
        },
    ],
}


# ── DOMAIN METADATA (returned in /status and response headers) ────────────────

DOMAIN_METADATA: Dict[str, Dict] = {
    "seismic": {
        "label":        "Seismic Precursor Detection",
        "applications": ["Megathrust monitoring", "Crustal earthquake precursor detection",
                         "Subduction zone early warning", "Seismic network integration"],
        "data_sources": ["IRIS/FDSN BHZ waveforms", "Regional seismograph networks",
                         "Magnitude catalogues (local/moment)"],
        "iris_ready":   True,
        "notes":        "Primary retrospective validation target. Tōhoku IRIS/FDSN run is next milestone.",
    },
    "volcanic": {
        "label":        "Volcanic Eruption Precursor Detection",
        "applications": ["Long-period tremor monitoring", "Sub-glacial eruption precursors",
                         "Conduit pressurisation detection", "Volcanic observatory integration"],
        "data_sources": ["IRIS/FDSN BHZ waveforms", "IMO (Iceland Meteorological Office)",
                         "PHIVOLCS", "USGS Volcano Hazards Program"],
        "iris_ready":   True,
        "notes":        "Eyjafjallajökull retrospective waveform run planned after seismic validation.",
    },
    "structural": {
        "label":        "Structural Health & AE Monitoring",
        "applications": ["Progressive collapse precursor detection", "Bridge fatigue monitoring",
                         "Dam structural health monitoring", "Industrial AE monitoring"],
        "data_sources": ["Piezoelectric AE sensors", "Accelerometer arrays",
                         "MEMS vibration sensors", "Embedded structural sensors"],
        "iris_ready":   False,
        "notes":        "AE field data required — IRIS/FDSN does not apply. "
                        "Validation path requires partnered AE sensor deployment.",
    },
}

