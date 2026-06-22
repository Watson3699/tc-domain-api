"""
Triple-Convergence Acoustic Diagnostic Engine — Black-Box API
=============================================================
AW IP Holdings Inc. | Confidential

Endpoints
---------
GET  /status     — health check + engine version (no auth)
POST /analyse    — waveform → CCI + alert + sanitised channel scores
POST /validate   — synthetic historical event harness (sanitised)

Auth: X-API-Key header (set TC_API_KEY env var in Render dashboard)

Engine internals (weights, thresholds, k-ratio formula, raw channel
values) are NEVER returned in any response.

Note on engine state: a fresh TCEngine() is created per /analyse request.
Kalman and Ljung-Box history do not carry across requests — clean
independent scoring for each submission.
"""

import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from tc_engine_v2 import (
    BUILD_TAG,
    VERSION,
    TCEngine,
    sanitize_channel_for_api,   # public helper — no underscore import
    run_validation,
)

# ── APP ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Triple-Convergence Acoustic Diagnostic Engine API",
    description=(
        "Black-box CCI scoring service. "
        "Engine internals are proprietary — results only. "
        "AW IP Holdings Inc."
    ),
    version=VERSION,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    # PRIVATE NDA TESTING: allow_origins=["*"] is acceptable for restricted internal testing.
    # PRE-PUBLIC: replace with your dashboard domain, e.g.:
    # allow_origins=["https://your-dashboard-domain.com"],
    # Rate limiting and IP throttling should be handled at the Render / reverse-proxy layer.
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_START_TIME = time.time()

# ── AUTH ──────────────────────────────────────────────────────────────────────

_API_KEY = os.environ.get("TC_API_KEY", "")


def _require_api_key(x_api_key: str) -> None:
    if not _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on server.",
        )
    if x_api_key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


# ── REQUEST / RESPONSE SCHEMAS ────────────────────────────────────────────────

class AnalyseRequest(BaseModel):
    waveform: List[float] = Field(
        ...,
        description=(
            "1-D acoustic or seismic time-series as a float array. "
            "Minimum 64 samples, maximum 65536. Normalise to [-1, 1] before submission."
        ),
        min_length=64,
        max_length=65536,
    )
    magnitudes: Optional[List[float]] = Field(
        None,
        description=(
            "Optional event magnitude catalogue for the stress index channel. "
            "Must contain at least 5 values if provided. "
            "Synthesised from waveform envelope if omitted."
        ),
    )
    mc: float = Field(
        0.0,
        description="Completeness magnitude threshold (default 0.0).",
        ge=0.0,
        le=5.0,
    )

    @field_validator("waveform")
    @classmethod
    def waveform_finite(cls, v: List[float]) -> List[float]:
        if any(not np.isfinite(x) for x in v):
            raise ValueError("waveform must contain only finite values (no NaN or Inf).")
        if any(abs(x) > 1.0 for x in v):
            raise ValueError("waveform must be normalised to [-1, 1] before submission.")
        return v

    @field_validator("magnitudes")
    @classmethod
    def magnitudes_valid(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is None:
            return v
        if len(v) < 5:
            raise ValueError("magnitudes must contain at least 5 values if provided.")
        if any(not np.isfinite(x) for x in v):
            raise ValueError("magnitudes must contain only finite values (no NaN or Inf).")
        return v


class AnalyseResponse(BaseModel):
    cci:          float = Field(..., description="Composite Criticality Index 0–1.")
    alert_level:  str   = Field(..., description="NOMINAL | ADVISORY | WARNING | CRITICAL")
    channels:     dict  = Field(..., description="Per-channel normalised scores (sanitised).")
    sample_count: int   = Field(..., description="Number of samples processed.")
    engine_build: str   = Field(..., description="Engine build tag.")
    audit_hash:   str   = Field(..., description="SHA-256 audit hash for this result.")
    timestamp:    float = Field(..., description="Unix epoch of analysis.")


class ValidateResponse(BaseModel):
    engine_build:    str
    events_tested:   int
    events_sim_pass: int
    results:         Dict[str, Any]
    disclaimer:      str


class StatusResponse(BaseModel):
    status:       str
    engine_build: str
    version:      str
    uptime_s:     float


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/status", response_model=StatusResponse, tags=["Health"])
def get_status():
    """Health check. No authentication required."""
    return StatusResponse(
        status="ok",
        engine_build=BUILD_TAG,
        version=VERSION,
        uptime_s=round(time.time() - _START_TIME, 1),
    )


@app.post("/analyse", response_model=AnalyseResponse, tags=["Engine"])
def analyse(
    body: AnalyseRequest,
    x_api_key: str = Header(..., description="API key via X-API-Key header"),
):
    """
    Submit a waveform for CCI analysis.

    Returns the Composite Criticality Index (CCI), alert level, and
    sanitised per-channel scores. Engine internals — weights, thresholds,
    k-ratio formula, raw channel values — are never returned.

    A fresh engine instance is created per request: Kalman and Ljung-Box
    history do not carry across submissions.

    **Waveform:** JSON float array, 64–65536 samples, normalised to [-1, 1].
    """
    _require_api_key(x_api_key)

    waveform   = np.array(body.waveform,   dtype=float)
    magnitudes = np.array(body.magnitudes, dtype=float) if body.magnitudes is not None else None

    # Fresh engine per request — no cross-request state contamination
    engine = TCEngine()
    result = engine.analyse(waveform=waveform, magnitudes=magnitudes, mc=body.mc)

    return AnalyseResponse(
        cci=round(result.cci, 4),
        alert_level=result.alert_level,
        channels={k: sanitize_channel_for_api(k, v) for k, v in result.channels.items()},
        sample_count=result.sample_count,
        engine_build=BUILD_TAG,
        audit_hash=result.audit_hash,
        timestamp=result.timestamp,
    )


@app.post("/validate", response_model=ValidateResponse, tags=["Validation"])
def validate(
    x_api_key: str = Header(..., description="API key via X-API-Key header"),
):
    """
    Run the synthetic historical event validation harness.

    Executes three calibrated synthetic precursor signals and returns
    sanitised per-event CCI scores and alert levels. Internal severity
    scales, seeds, and raw channel values are not returned.

    Each event uses an independent engine instance — no state sharing.

    **Important:** Results are from physically motivated synthetic signals —
    not raw IRIS/FDSN instrument data. IRIS retrospective validation is in
    progress under TC-VAL-PROTO-001. SIM-HARNESS-PASS does not constitute
    empirical instrument-data validation.
    """
    _require_api_key(x_api_key)

    results  = run_validation()
    sim_pass = sum(1 for r in results.values() if r["status"] == "SIM-HARNESS-PASS")

    return ValidateResponse(
        engine_build=BUILD_TAG,
        events_tested=len(results),
        events_sim_pass=sim_pass,
        results=results,
        disclaimer=(
            "Synthetic simulation results only. Channel values and CCI scores are outputs "
            "from physically motivated synthetic signal runs calibrated to published event "
            "signatures. IRIS/FDSN retrospective validation is pending under TC-VAL-PROTO-001. "
            "SIM-HARNESS-PASS does not constitute empirical instrument-data validation."
        ),
    )

