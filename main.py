"""
Triple-Convergence Acoustic Diagnostic Engine — Domain API
===========================================================
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret

Black-box multi-domain CCI scoring service.
Engine internals (weights, thresholds, k-ratio formula, raw channel
values) are NEVER returned in any response.

Domains
-------
  seismic    — megathrust, crustal earthquake precursor detection
  volcanic   — long-period tremor, conduit pressurisation, eruption precursor
  structural — acoustic emission, progressive collapse, fatigue monitoring

Endpoints
---------
GET  /status                        — health check + engine version (no auth)
GET  /domains                       — list available domains and metadata
POST /analyse/{domain}              — waveform → CCI + alert + sanitised channels
POST /validate/{domain}             — synthetic domain harness (sanitised)
POST /validate/all                  — run all three domain harnesses

Auth: X-API-Key header (set TC_API_KEY env var in Render dashboard)
"""

import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI, Header, HTTPException, Path, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from tc_engine_v2 import (
    BUILD_TAG,
    VERSION,
    TCEngine,
    sanitize_channel_for_api,
)
from domain_config import DOMAINS, DOMAIN_METADATA, get_weights
from domain_harness import run_domain_validation

# ── APP ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Triple-Convergence Acoustic Diagnostic Engine — Domain API",
    description=(
        "Multi-domain black-box CCI scoring service. "
        "Covers seismic, volcanic, and structural acoustic emission monitoring. "
        "Engine internals are proprietary — results only. "
        "AW IP Holdings Inc."
    ),
    version=VERSION,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to dashboard domain before public launch
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


def _require_domain(domain: str) -> str:
    if domain not in DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown domain '{domain}'. Valid domains: {list(DOMAINS)}",
        )
    return domain


# ── SCHEMAS ───────────────────────────────────────────────────────────────────

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
    domain:       str
    cci:          float
    alert_level:  str
    channels:     dict
    sample_count: int
    engine_build: str
    audit_hash:   str
    timestamp:    float


class ValidateResponse(BaseModel):
    domain:          str
    engine_build:    str
    events_tested:   int
    events_sim_pass: int
    negative_controls_pass: int
    results:         List[Dict[str, Any]]
    disclaimer:      str


class StatusResponse(BaseModel):
    status:       str
    engine_build: str
    version:      str
    uptime_s:     float
    domains:      List[str]


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/status", response_model=StatusResponse, tags=["Health"])
def get_status():
    """Health check. No authentication required."""
    return StatusResponse(
        status="ok",
        engine_build=BUILD_TAG,
        version=VERSION,
        uptime_s=round(time.time() - _START_TIME, 1),
        domains=list(DOMAINS),
    )


@app.get("/domains", tags=["Domains"])
def list_domains(
    x_api_key: str = Header(..., description="API key via X-API-Key header"),
):
    """
    List available monitoring domains and their metadata.
    Returns domain labels, applications, data sources, and validation status.
    """
    _require_api_key(x_api_key)
    return {
        "engine_build": BUILD_TAG,
        "domains": DOMAIN_METADATA,
    }


@app.post("/analyse/{domain}", response_model=AnalyseResponse, tags=["Engine"])
def analyse(
    domain: str = Path(..., description="Monitoring domain: seismic | volcanic | structural"),
    body: AnalyseRequest = ...,
    x_api_key: str = Header(..., description="API key via X-API-Key header"),
):
    """
    Submit a waveform for domain-specific CCI analysis.

    Returns the Composite Criticality Index (CCI), alert level, and
    sanitised per-channel scores for the specified domain.

    Engine internals — weights, thresholds, k-ratio formula, raw channel
    values — are never returned.

    A fresh engine instance is created per request.

    **Domains:** seismic | volcanic | structural
    **Waveform:** JSON float array, 64–65536 samples, normalised to [-1, 1].
    """
    _require_api_key(x_api_key)
    _require_domain(domain)

    waveform   = np.array(body.waveform, dtype=float)
    magnitudes = np.array(body.magnitudes, dtype=float) if body.magnitudes is not None else None

    engine = TCEngine()
    result = engine.analyse(waveform=waveform, magnitudes=magnitudes, mc=body.mc)

    return AnalyseResponse(
        domain=domain,
        cci=round(result.cci, 4),
        alert_level=result.alert_level,
        channels={k: sanitize_channel_for_api(k, v) for k, v in result.channels.items()},
        sample_count=result.sample_count,
        engine_build=BUILD_TAG,
        audit_hash=result.audit_hash,
        timestamp=result.timestamp,
    )


@app.post("/validate/{domain}", response_model=ValidateResponse, tags=["Validation"])
def validate_domain(
    domain: str = Path(..., description="Monitoring domain: seismic | volcanic | structural"),
    x_api_key: str = Header(..., description="API key via X-API-Key header"),
):
    """
    Run the synthetic validation harness for a specific domain.

    Executes calibrated synthetic precursor signals plus negative controls
    for the domain. Returns sanitised per-event CCI scores and alert levels.

    Internal severity scales, seeds, and raw channel values are not returned.
    Each event uses an independent engine instance — no state sharing.

    **Important:** Results are from physically motivated synthetic signals —
    not raw IRIS/FDSN instrument data. IRIS retrospective validation is in
    progress under TC-VAL-PROTO-001.
    """
    _require_api_key(x_api_key)
    _require_domain(domain)

    results  = run_domain_validation(domain)
    sim_pass = sum(1 for r in results if r["status"] == "SIM-HARNESS-PASS")
    nc_pass  = sum(1 for r in results if r["status"] in ("NC-PASS", "NC-STUB-LIMITED")
                   and r["is_negative_control"])

    return ValidateResponse(
        domain=domain,
        engine_build=BUILD_TAG,
        events_tested=len(results),
        events_sim_pass=sim_pass,
        negative_controls_pass=nc_pass,
        results=results,
        disclaimer=(
            "Synthetic simulation results only. CCI scores are outputs from physically "
            "motivated synthetic signal runs calibrated to published event signatures. "
            "IRIS/FDSN retrospective validation is pending under TC-VAL-PROTO-001. "
            "SIM-HARNESS-PASS does not constitute empirical instrument-data validation."
        ),
    )


@app.post("/validate/all", response_model=Dict[str, Any], tags=["Validation"])
def validate_all(
    x_api_key: str = Header(..., description="API key via X-API-Key header"),
):
    """
    Run the synthetic validation harness across all three domains.

    Returns a combined sanitised result set for seismic, volcanic,
    and structural domains in a single call.
    """
    _require_api_key(x_api_key)

    combined = {}
    for domain in DOMAINS:
        results  = run_domain_validation(domain)
        sim_pass = sum(1 for r in results if r["status"] == "SIM-HARNESS-PASS")
        nc_pass  = sum(1 for r in results if r["status"] in ("NC-PASS", "NC-STUB-LIMITED")
                       and r["is_negative_control"])
        combined[domain] = {
            "events_tested":          len(results),
            "events_sim_pass":        sim_pass,
            "negative_controls_pass": nc_pass,
            "results":                results,
        }

    return {
        "engine_build": BUILD_TAG,
        "domains":      combined,
        "disclaimer": (
            "Synthetic simulation results only. IRIS/FDSN retrospective validation "
            "is pending under TC-VAL-PROTO-001."
        ),
    }

