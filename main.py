"""
main.py
=======
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
PRECEPT Platform API — v3.1.0

Endpoints
---------
Public (no auth):
  GET  /status                       Engine health and build info.
  GET  /domains                      List available analysis domains.

Protected (X-API-Key required):
  POST /analyse/{domain}             Single-window screening analysis.
  POST /analyse/csv/{domain}         CSV waveform upload screening analysis.
  POST /validate/{domain}            Single-domain synthetic validation.
  POST /validate/all                 Full three-event validation harness.

  POST /session/create               Create persistent streaming session.
  POST /session/{session_id}/push    Push waveform window to session.
  GET  /session/{session_id}/status  Get current session state.
  DELETE /session/{session_id}       Terminate session and free state.

One-shot vs Streaming
---------------------
/analyse endpoints are screening only. A fresh TCEngine is created per
request with no history — persistence gate and surrogate gate are
disabled. Use streaming sessions for persistence-gated alert confirmation.

Streaming sessions retain a live TCEngine across multiple push calls.
Persistence gate and surrogate gate are active in session mode.

Authentication
--------------
All protected endpoints require header:  X-API-Key: <TC_API_KEY env var>

Trade secrets — never returned in any response:
  channel weights, thresholds, channel formulas, surrogate parameters,
  persistence gate parameters, band definitions.
"""
from __future__ import annotations

import io
import os
import time
import uuid
from typing import Dict, List, Optional

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from tc_engine_v3 import (
    TCEngine,
    run_validation,
    sanitize_channel_for_api,
    VERSION,
    BUILD_TAG,
)
from domain_weights import list_domains, get_domain_config

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PRECEPT Platform API",
    description=(
        "Triple-Convergence Acoustic Diagnostic Engine — "
        "Seismic / Volcanic / Structural domain analysis. "
        "AW IP Holdings Inc. Proprietary."
    ),
    version="3.1.0",
    docs_url=None,
    redoc_url=None,
)

# CORS — locked to portal origin.
# Update PRECEPT_ALLOWED_ORIGIN env var to match your buyer portal domain.
_ALLOWED_ORIGIN = os.environ.get(
    "PRECEPT_ALLOWED_ORIGIN", "https://watson3699.github.io"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_ALLOWED_ORIGIN],
    allow_origin_regex=r"^http://localhost(:\d+)?$",
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

_START_TIME = time.time()

# ── Auth ──────────────────────────────────────────────────────────────────────

_API_KEY = os.environ.get("TC_API_KEY", "")


def _require_key(x_api_key: str = Header(...)) -> None:
    if not _API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured.")
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized.")


# ── Session store (in-process, per-instance) ──────────────────────────────────
# Note: Render free tier has one instance. For multi-instance deployments,
# replace with Redis or a shared store.

_SESSIONS: Dict[str, dict] = {}
_SESSION_TTL_S = 3600   # 1 hour idle expiry
_MAX_SESSIONS  = 50     # hard cap — prevents memory exhaustion on Render


def _expire_sessions() -> None:
    """Remove sessions idle longer than TTL."""
    now  = time.time()
    dead = [sid for sid, s in _SESSIONS.items()
            if now - s["last_active"] > _SESSION_TTL_S]
    for sid in dead:
        del _SESSIONS[sid]


# ── Request / Response models ─────────────────────────────────────────────────

class AnalyseRequest(BaseModel):
    waveform:   List[float] = Field(..., min_length=16, max_length=20000,
                                    description="Signal samples (min 16, max 20000). Must be normalized to [-1, 1].")
    magnitudes: Optional[List[float]] = Field(
        None, description="Optional magnitude catalogue (min 5 if provided).")
    mc:         float = Field(0.0, ge=-10, le=10, description="Magnitude of completeness.")
    fs:         float = Field(100.0, gt=0, le=100_000, description="Sample rate (Hz).")
    timestamp:  Optional[float] = Field(None, description="Unix timestamp.")

    @field_validator("magnitudes")
    @classmethod
    def _check_mags(cls, v):
        if v is not None and len(v) < 5:
            raise ValueError("magnitudes must contain at least 5 values.")
        return v


class AnalyseResponse(BaseModel):
    domain:             str
    cci:                float
    alert_level:        str
    raw_alert_level:    str
    persistence_score:  float
    confidence:         float
    surrogate_z:        float
    surrogate_tested:   bool
    channels:           dict
    audit_hash:         str
    sample_count:       int
    timestamp:          float
    engine_build:       str
    disclaimer:         str


class SessionCreateRequest(BaseModel):
    domain: str   = Field(..., description="Analysis domain: seismic, volcanic, or structural.")
    fs:     float = Field(100.0, gt=0, le=100_000, description="Sample rate (Hz).")


class SessionPushRequest(BaseModel):
    waveform:   List[float] = Field(..., min_length=16, max_length=20000,
                                    description="Signal samples (min 16, max 20000). Must be normalized to [-1, 1].")
    magnitudes: Optional[List[float]] = None
    mc:         float = 0.0
    timestamp:  Optional[float] = None

    @field_validator("magnitudes")
    @classmethod
    def _check_mags(cls, v):
        if v is not None and len(v) < 5:
            raise ValueError("magnitudes must contain at least 5 values.")
        return v


# ── Waveform normalization guard ──────────────────────────────────────────────

def _check_normalized(waveform: np.ndarray) -> None:
    """Raise if waveform is not normalized to [-1, 1]."""
    peak = float(np.max(np.abs(waveform)))
    if peak > 1.0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Waveform must be normalized to [-1, 1]. "
                f"Peak amplitude detected: {peak:.4f}. "
                "Divide by max(abs(waveform)) before submitting."
            ),
        )


# ── Shared response builder ───────────────────────────────────────────────────

def _build_response(out, mode: str = "session") -> dict:
    disclaimer = (
        "Engine output is based on signal processing of provided waveform data. "
        "IRIS/FDSN retrospective validation pending (TC-VAL-PROTO-001). "
        "SIM-HARNESS-PASS results do not constitute empirical instrument-data validation."
    )
    if mode == "screening":
        disclaimer = (
            "Single-window analysis is screening only. "
            "Streaming sessions are required for persistence-gated alert confirmation. "
            + disclaimer
        )
    return {
        "domain":            out.domain,
        "cci":               round(out.cci, 4),
        "alert_level":       out.alert_level,
        "raw_alert_level":   out.raw_alert_level,
        "persistence_score": out.persistence_score,
        "confidence":        out.confidence,
        "surrogate_z":       out.surrogate_z,
        "surrogate_tested":  out.surrogate_tested,
        "channels":          {k: sanitize_channel_for_api(k, v)
                              for k, v in out.channels.items()},
        "audit_hash":        out.audit_hash,
        "sample_count":      out.sample_count,
        "timestamp":         out.timestamp,
        "engine_build":      BUILD_TAG,
        "disclaimer":        disclaimer,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/status")
def status():
    return {
        "status":       "ok",
        "platform":     "PRECEPT",
        "engine":       "SENTINEL",
        "engine_build": BUILD_TAG,
        "version":      VERSION,
        "uptime_s":     round(time.time() - _START_TIME, 1),
        "domains":      list(list_domains().keys()),
        "active_sessions": len(_SESSIONS),
    }


@app.get("/domains")
def domains():
    return {
        "domains": list_domains(),
        "note": (
            "Domain-specific CCI weights are proprietary. "
            "Contact AW IP Holdings Inc. for licensing information."
        ),
    }


# ── One-shot screening endpoints ──────────────────────────────────────────────

@app.post("/analyse/{domain}", response_model=AnalyseResponse,
          dependencies=[Depends(_require_key)])
def analyse(domain: str, body: AnalyseRequest):
    """
    Single-window screening analysis. Fresh engine per request — no
    persistence history. Surrogate gate disabled. For persistence-gated
    alert confirmation use /session endpoints.
    """
    try:
        get_domain_config(domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    waveform = np.array(body.waveform, dtype=float)
    _check_normalized(waveform)

    engine = TCEngine(domain=domain, fs=body.fs, enable_surrogate_gate=False)
    mags   = np.array(body.magnitudes) if body.magnitudes else None

    try:
        out = engine.analyse(
            waveform=waveform,
            magnitudes=mags,
            mc=body.mc,
            timestamp=body.timestamp,
            apply_surrogate_gate=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return _build_response(out, mode="screening")


@app.post("/analyse/csv/{domain}", response_model=AnalyseResponse,
          dependencies=[Depends(_require_key)])
def analyse_csv(domain: str, file: UploadFile = File(...),
                mc: float = 0.0, fs: float = 100.0):
    """
    Single-window CSV waveform screening. Same constraints as /analyse —
    screening only, no persistence. Waveform must be normalized to [-1, 1].
    """
    try:
        get_domain_config(domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if fs <= 0 or fs > 100_000:
        raise HTTPException(status_code=422,
                            detail="fs must be between 0 and 100000 Hz.")
    if not -10 <= mc <= 10:
        raise HTTPException(status_code=422,
                            detail="mc must be between -10 and 10.")

    try:
        contents = file.file.read()
        if len(contents) > 2_000_000:
            raise HTTPException(status_code=413, detail="CSV file too large. Maximum 2 MB.")
        data     = np.genfromtxt(io.BytesIO(contents), delimiter=",")
        data     = data.flatten()
        data     = data[np.isfinite(data)]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {e}")

    if len(data) < 16:
        raise HTTPException(status_code=422,
                            detail="CSV must contain at least 16 finite values.")

    _check_normalized(data)

    engine = TCEngine(domain=domain, fs=fs, enable_surrogate_gate=False)
    try:
        out = engine.analyse(waveform=data, mc=mc, apply_surrogate_gate=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return _build_response(out, mode="screening")


# ── Validation endpoints ──────────────────────────────────────────────────────

@app.post("/validate/{domain}", dependencies=[Depends(_require_key)])
def validate_domain(domain: str):
    """Run synthetic validation harness for one domain."""
    try:
        get_domain_config(domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    all_results    = run_validation()
    domain_results = {
        k: v for k, v in all_results.items()
        if v.get("domain", "").lower() == domain.lower()
    }

    if not domain_results:
        raise HTTPException(status_code=404,
                            detail=f"No validation events for domain '{domain}'.")

    return {"domain": domain, "results": domain_results, "engine_build": BUILD_TAG}


@app.post("/validate/all", dependencies=[Depends(_require_key)])
def validate_all():
    """Run full three-event synthetic validation harness."""
    results = run_validation()
    return {
        "results":      results,
        "engine_build": BUILD_TAG,
        "disclaimer": (
            "All results are SIM-HARNESS outputs using synthetic precursor "
            "profiles. IRIS/FDSN retrospective validation is pending under "
            "TC-VAL-PROTO-001. These results do not constitute empirical "
            "instrument-data validation."
        ),
    }


# ── Streaming session endpoints ───────────────────────────────────────────────

@app.post("/session/create", dependencies=[Depends(_require_key)])
def session_create(body: SessionCreateRequest):
    """
    Create a persistent streaming session. Returns a session_id.

    The session retains a live TCEngine — Kalman, Ljung-Box, AttractorDrift,
    PLV, and persistence state all accumulate across push calls.
    Surrogate gate is active: WARNING/CRITICAL alerts are tested against
    IAAFT surrogates before being confirmed.

    Sessions expire after 1 hour of inactivity.
    """
    _expire_sessions()

    if len(_SESSIONS) >= _MAX_SESSIONS:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum active sessions ({_MAX_SESSIONS}) reached. "
                   "Delete an existing session or wait for idle sessions to expire."
        )

    try:
        get_domain_config(body.domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {
        "engine":      TCEngine(domain=body.domain, fs=body.fs,
                                enable_surrogate_gate=True),
        "domain":      body.domain,
        "fs":          body.fs,
        "created_at":  time.time(),
        "last_active": time.time(),
        "push_count":  0,
        "last_output": None,
    }

    return {
        "session_id":  session_id,
        "domain":      body.domain,
        "fs":          body.fs,
        "engine_build": BUILD_TAG,
        "note": (
            "Push waveform windows to /session/{session_id}/push. "
            "Persistence gate requires multiple windows before alert confirmation."
        ),
    }


@app.post("/session/{session_id}/push", dependencies=[Depends(_require_key)])
def session_push(session_id: str, body: SessionPushRequest):
    """
    Push a waveform window to an active session.

    Each push updates engine state (Kalman, Ljung-Box, AttractorDrift, PLV,
    persistence). Returns current CCI, alert level, and all channel scores.
    Surrogate gate fires on WARNING/CRITICAL — expect slightly higher latency
    on those windows.
    """
    _expire_sessions()

    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404,
                            detail="Session not found or expired.")

    sess    = _SESSIONS[session_id]
    engine: TCEngine = sess["engine"]

    waveform = np.array(body.waveform, dtype=float)
    _check_normalized(waveform)

    mags = np.array(body.magnitudes) if body.magnitudes else None

    try:
        out = engine.analyse(
            waveform=waveform,
            magnitudes=mags,
            mc=body.mc,
            timestamp=body.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    sess["last_active"] = time.time()
    sess["push_count"]  += 1
    sess["last_output"] = out

    response = _build_response(out, mode="session")
    response["session_id"]  = session_id
    response["push_count"]  = sess["push_count"]
    return response


@app.get("/session/{session_id}/status", dependencies=[Depends(_require_key)])
def session_status(session_id: str):
    """Get current state of an active session."""
    _expire_sessions()

    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404,
                            detail="Session not found or expired.")

    sess = _SESSIONS[session_id]
    out  = sess["last_output"]

    base = {
        "session_id":   session_id,
        "domain":       sess["domain"],
        "push_count":   sess["push_count"],
        "created_at":   sess["created_at"],
        "last_active":  sess["last_active"],
        "engine_build": BUILD_TAG,
    }

    if out is not None:
        base.update({
            "cci":               round(out.cci, 4),
            "alert_level":       out.alert_level,
            "raw_alert_level":   out.raw_alert_level,
            "persistence_score": out.persistence_score,
            "confidence":        out.confidence,
            "surrogate_z":       out.surrogate_z,
            "surrogate_tested":  out.surrogate_tested,
            "channels":          {k: sanitize_channel_for_api(k, v)
                                  for k, v in out.channels.items()},
            "audit_hash":        out.audit_hash,
        })
    else:
        base["note"] = "No windows pushed yet."

    return base


@app.delete("/session/{session_id}", dependencies=[Depends(_require_key)])
def session_delete(session_id: str):
    """Terminate a session and free its engine state."""
    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404,
                            detail="Session not found or expired.")
    del _SESSIONS[session_id]
    return {"session_id": session_id, "status": "terminated"}
