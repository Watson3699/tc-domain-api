"""
main.py
=======
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
PRECEPT Platform API — v3.2.0

Endpoints
---------
Public (no auth):
  GET  /status                           Engine health and build info.
  GET  /domains                          List available analysis domains.

  POST /demo/session/create              Create a public demo session (synthetic waveforms only).
  POST /demo/session/{id}/scan           Advance one synthetic window through the real engine.
  POST /demo/validate/all                Run public verification harness (rate-limited).

Protected (X-API-Key required):
  POST /analyse/{domain}                 Single-window screening analysis.
  POST /analyse/csv/{domain}             CSV waveform upload screening analysis.
  POST /validate/{domain}                Single-domain synthetic validation.
  POST /validate/all                     Full three-event validation harness.

  POST /session/create                   Create persistent streaming session.
  POST /session/{session_id}/push        Push waveform window to session.
  GET  /session/{session_id}/status      Get current session state.
  DELETE /session/{session_id}           Terminate session and free state.

Trial (PRECEPT_TRIAL_CODE required):
  POST /trial/session/create             Create buyer trial session (real waveforms).
  POST /trial/session/{id}/push          Push real waveform window (JSON body).
  GET  /trial/session/{id}/status        Get trial session state (X-Trial-Code header).
  DELETE /trial/session/{id}             Terminate trial session (X-Trial-Code header).
  POST /trial/csv/{domain}               CSV upload screening (trial_code as form field).

Authentication
--------------
Protected endpoints require header: X-API-Key: <TC_API_KEY env var>
Trial endpoints require header:     X-Trial-Code: <PRECEPT_TRIAL_CODE env var>
  or body field trial_code for create/push.

Trade secrets — never returned in any response:
  channel weights, thresholds, channel formulas, surrogate parameters,
  persistence gate parameters, band definitions.
"""
from __future__ import annotations

import io
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

import numpy as np
from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request, Response, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from tc_engine_v3 import (
    TCEngine,
    run_validation,
    sanitize_channel_for_api,
    VERSION,
    BUILD_TAG,
)
from domain_weights import list_domains, get_domain_config
from synthetic_demo import get_window, get_assets, DEMO_PROFILES

logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PRECEPT Platform API",
    description=(
        "Triple-Convergence Acoustic Diagnostic Engine — "
        "Seismic / Volcanic / Structural domain analysis. "
        "AW IP Holdings Inc. Proprietary."
    ),
    version="3.2.0",
    docs_url=None,
    redoc_url=None,
)

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


# ── Protected session store ───────────────────────────────────────────────────

_SESSIONS: Dict[str, dict] = {}
_SESSION_TTL_S = 3600
_MAX_SESSIONS  = 50


def _expire_sessions() -> None:
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
    waveform:   List[float] = Field(..., min_length=16, max_length=20000)
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

def _build_response(out: Any, mode: str = "session") -> dict:
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


# ── Public routes ─────────────────────────────────────────────────────────────

@app.get("/status")
def status_route():
    return {
        "status":          "ok",
        "platform":        "PRECEPT",
        "engine":          "SENTINEL",
        "engine_build":    BUILD_TAG,
        "version":         VERSION,
        "uptime_s":        round(time.time() - _START_TIME, 1),
        "domains":         list(list_domains().keys()),
        "active_sessions": len(_SESSIONS),
    }


@app.get("/domains")
def domains_route():
    return {
        "domains": list_domains(),
        "note": (
            "Domain-specific CCI weights are proprietary. "
            "Contact AW IP Holdings Inc. for licensing information."
        ),
    }


# ── Demo session store (public, rate-limited) ─────────────────────────────────

_DEMO_SESSIONS: Dict[str, dict] = {}
_DEMO_SESSION_TTL_S = 1800
_MAX_DEMO_SESSIONS  = 200

_DEMO_RATE: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=30))
_DEMO_RATE_WINDOW_S = 60
_DEMO_RATE_MAX      = 20


def _expire_demo_sessions() -> None:
    now  = time.time()
    dead = [sid for sid, s in _DEMO_SESSIONS.items()
            if now - s["last_active"] > _DEMO_SESSION_TTL_S]
    for sid in dead:
        del _DEMO_SESSIONS[sid]


def _prune_rate_dict(rate_dict: Dict, window_s: float) -> None:
    """Remove IPs with no recent requests to prevent unbounded memory growth."""
    now      = time.time()
    stale    = [ip for ip, q in rate_dict.items()
                if not q or now - q[-1] > window_s * 10]
    for ip in stale:
        del rate_dict[ip]


def _check_demo_rate(request: Request) -> None:
    ip  = request.client.host if request.client else "unknown"
    now = time.time()
    # Prune stale IPs periodically (1-in-100 chance per request — cheap)
    if len(_DEMO_RATE) > 500 and hash(ip) % 100 == 0:
        _prune_rate_dict(_DEMO_RATE, _DEMO_RATE_WINDOW_S)
    q   = _DEMO_RATE[ip]
    while q and now - q[0] > _DEMO_RATE_WINDOW_S:
        q.popleft()
    if len(q) >= _DEMO_RATE_MAX:
        raise HTTPException(status_code=429,
                            detail="Demo rate limit reached. Try again shortly.")
    q.append(now)


class DemoSessionCreateRequest(BaseModel):
    domain: str = Field(..., description="seismic, volcanic, or structural")
    asset:  str = Field(..., description="Demo asset key from DEMO_PROFILES")


@app.post("/demo/session/create")
def demo_session_create(body: DemoSessionCreateRequest, request: Request):
    _check_demo_rate(request)
    _expire_demo_sessions()

    if len(_DEMO_SESSIONS) >= _MAX_DEMO_SESSIONS:
        raise HTTPException(status_code=429,
                            detail="Demo capacity reached. Try again shortly.")
    try:
        get_domain_config(body.domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    known_assets = get_assets(body.domain)
    if body.asset not in known_assets:
        raise HTTPException(status_code=422,
                            detail=f"Unknown demo asset '{body.asset}' for domain '{body.domain}'. "
                                   f"Known assets: {known_assets}")

    session_id = str(uuid.uuid4())
    _DEMO_SESSIONS[session_id] = {
        "engine":      TCEngine(domain=body.domain, fs=100.0, enable_surrogate_gate=True),
        "domain":      body.domain,
        "asset":       body.asset,
        "scan_index":  0,
        "created_at":  time.time(),
        "last_active": time.time(),
    }
    return {
        "session_id":   session_id,
        "domain":       body.domain,
        "asset":        body.asset,
        "engine_build": BUILD_TAG,
    }


@app.post("/demo/session/{session_id}/scan")
def demo_session_scan(session_id: str, request: Request):
    _check_demo_rate(request)
    _expire_demo_sessions()

    if session_id not in _DEMO_SESSIONS:
        raise HTTPException(status_code=404,
                            detail="Demo session not found or expired.")

    sess         = _DEMO_SESSIONS[session_id]
    engine: TCEngine = sess["engine"]

    # Unpack tuple — get_window now returns (window, metadata)
    window, demo_meta = get_window(sess["domain"], sess["asset"], sess["scan_index"])

    try:
        out = engine.analyse(waveform=window)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    sess["scan_index"]  += 1
    sess["last_active"]  = time.time()

    response             = _build_response(out, mode="session")
    response["session_id"]  = session_id
    response["scan_index"]  = sess["scan_index"]
    response["demo_meta"]   = demo_meta   # archetype, severity, onset_frac, disclaimer, etc.
    response["note"]        = "Demo session — synthetic precursor waveform, real engine output."
    return response


@app.delete("/demo/session/{session_id}")
def demo_session_delete(session_id: str):
    if session_id not in _DEMO_SESSIONS:
        raise HTTPException(status_code=404,
                            detail="Demo session not found or expired.")
    del _DEMO_SESSIONS[session_id]
    return {"session_id": session_id, "status": "terminated"}


# ── Protected screening endpoints ─────────────────────────────────────────────

@app.post("/analyse/{domain}", response_model=AnalyseResponse,
          dependencies=[Depends(_require_key)])
def analyse(domain: str, body: AnalyseRequest):
    try:
        get_domain_config(domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    waveform = np.array(body.waveform, dtype=float)
    _check_normalized(waveform)

    engine = TCEngine(domain=domain, fs=body.fs, enable_surrogate_gate=False)
    mags   = np.array(body.magnitudes) if body.magnitudes else None

    try:
        out = engine.analyse(waveform=waveform, magnitudes=mags,
                             mc=body.mc, timestamp=body.timestamp,
                             apply_surrogate_gate=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return _build_response(out, mode="screening")


@app.post("/analyse/csv/{domain}", response_model=AnalyseResponse,
          dependencies=[Depends(_require_key)])
def analyse_csv(domain: str, file: UploadFile = File(...),
                mc: float = 0.0, fs: float = 100.0):
    try:
        get_domain_config(domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if fs <= 0 or fs > 100_000:
        raise HTTPException(status_code=422, detail="fs must be between 0 and 100000 Hz.")
    if not -10 <= mc <= 10:
        raise HTTPException(status_code=422, detail="mc must be between -10 and 10.")

    try:
        contents = file.file.read()
        if len(contents) > 2_000_000:
            raise HTTPException(status_code=413, detail="CSV file too large. Maximum 2 MB.")
        data = np.genfromtxt(io.BytesIO(contents), delimiter=",")
        data = data.flatten()
        data = data[np.isfinite(data)]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {e}")

    if len(data) < 16:
        raise HTTPException(status_code=422, detail="CSV must contain at least 16 finite values.")

    _check_normalized(data)
    engine = TCEngine(domain=domain, fs=fs, enable_surrogate_gate=False)
    try:
        out = engine.analyse(waveform=data, mc=mc, apply_surrogate_gate=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return _build_response(out, mode="screening")


# ── Protected validation endpoints ────────────────────────────────────────────

@app.post("/validate/{domain}", dependencies=[Depends(_require_key)])
def validate_domain(domain: str):
    try:
        get_domain_config(domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    all_results    = run_validation()
    domain_results = {k: v for k, v in all_results.items()
                      if v.get("domain", "").lower() == domain.lower()}

    if not domain_results:
        raise HTTPException(status_code=404,
                            detail=f"No validation events for domain '{domain}'.")

    return {"domain": domain, "results": domain_results, "engine_build": BUILD_TAG}


@app.post("/validate/all", dependencies=[Depends(_require_key)])
def validate_all():
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


# ── Protected streaming session endpoints ─────────────────────────────────────

@app.post("/session/create", dependencies=[Depends(_require_key)])
def session_create(body: SessionCreateRequest):
    _expire_sessions()

    if len(_SESSIONS) >= _MAX_SESSIONS:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum active sessions ({_MAX_SESSIONS}) reached.")

    try:
        get_domain_config(body.domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {
        "engine":      TCEngine(domain=body.domain, fs=body.fs, enable_surrogate_gate=True),
        "domain":      body.domain,
        "fs":          body.fs,
        "created_at":  time.time(),
        "last_active": time.time(),
        "push_count":  0,
        "last_output": None,
    }

    return {
        "session_id":   session_id,
        "domain":       body.domain,
        "fs":           body.fs,
        "engine_build": BUILD_TAG,
        "note": (
            "Push waveform windows to /session/{session_id}/push. "
            "Persistence gate requires multiple windows before alert confirmation."
        ),
    }


@app.post("/session/{session_id}/push", dependencies=[Depends(_require_key)])
def session_push(session_id: str, body: SessionPushRequest):
    _expire_sessions()

    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    sess    = _SESSIONS[session_id]
    engine: TCEngine = sess["engine"]

    waveform = np.array(body.waveform, dtype=float)
    _check_normalized(waveform)
    mags = np.array(body.magnitudes) if body.magnitudes else None

    try:
        out = engine.analyse(waveform=waveform, magnitudes=mags,
                             mc=body.mc, timestamp=body.timestamp)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    sess["last_active"] = time.time()
    sess["push_count"]  += 1
    sess["last_output"] = out

    response = _build_response(out, mode="session")
    response["session_id"] = session_id
    response["push_count"] = sess["push_count"]
    return response


@app.get("/session/{session_id}/status", dependencies=[Depends(_require_key)])
def session_status(session_id: str):
    _expire_sessions()

    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

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
    if session_id not in _SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    del _SESSIONS[session_id]
    return {"session_id": session_id, "status": "terminated"}


# ── Trial endpoints (PRECEPT_TRIAL_CODE gated) ────────────────────────────────

_TRIAL_CODE = os.environ.get("PRECEPT_TRIAL_CODE", "")

_TRIAL_SESSIONS: Dict[str, dict] = {}
_TRIAL_SESSION_TTL_S = 7200
_MAX_TRIAL_SESSIONS  = 50

_TRIAL_RATE: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=120))
_TRIAL_RATE_WINDOW_S = 60
_TRIAL_RATE_MAX      = 60


def _check_trial_code(trial_code: str) -> None:
    if not _TRIAL_CODE:
        raise HTTPException(status_code=500, detail="Trial access not configured.")
    if trial_code != _TRIAL_CODE:
        raise HTTPException(status_code=401, detail="Invalid trial code.")


def _expire_trial_sessions() -> None:
    now  = time.time()
    dead = [sid for sid, s in _TRIAL_SESSIONS.items()
            if now - s["last_active"] > _TRIAL_SESSION_TTL_S]
    for sid in dead:
        del _TRIAL_SESSIONS[sid]


def _check_trial_rate(request: Request) -> None:
    ip  = request.client.host if request.client else "unknown"
    now = time.time()
    if len(_TRIAL_RATE) > 200 and hash(ip) % 50 == 0:
        _prune_rate_dict(_TRIAL_RATE, _TRIAL_RATE_WINDOW_S)
    q   = _TRIAL_RATE[ip]
    while q and now - q[0] > _TRIAL_RATE_WINDOW_S:
        q.popleft()
    if len(q) >= _TRIAL_RATE_MAX:
        raise HTTPException(status_code=429,
                            detail="Trial rate limit reached. Try again shortly.")
    q.append(now)


class TrialSessionCreateRequest(BaseModel):
    domain:     str = Field(..., description="seismic, volcanic, or structural")
    trial_code: Optional[str] = Field(
        None,
        description="Trial code. Can also be supplied via X-Trial-Code header instead of body.")
    fs:         float = Field(100.0, gt=0, le=100_000)


@app.post("/trial/session/create")
def trial_session_create(
    body: TrialSessionCreateRequest,
    request: Request,
    x_trial_code: Optional[str] = Header(None, alias="X-Trial-Code"),
):
    """
    Create a buyer trial session.
    Auth: supply trial_code in JSON body OR as X-Trial-Code header.
    Header is preferred — body trial_code is accepted for backward compatibility.
    """
    _check_trial_rate(request)
    _check_trial_code(x_trial_code or body.trial_code or "")
    _expire_trial_sessions()

    if len(_TRIAL_SESSIONS) >= _MAX_TRIAL_SESSIONS:
        raise HTTPException(status_code=429,
                            detail="Trial capacity reached. Contact AW IP Holdings Inc.")
    try:
        get_domain_config(body.domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    session_id = str(uuid.uuid4())
    _TRIAL_SESSIONS[session_id] = {
        "engine":      TCEngine(domain=body.domain, fs=body.fs, enable_surrogate_gate=True),
        "domain":      body.domain,
        "fs":          body.fs,
        "created_at":  time.time(),
        "last_active": time.time(),
        "push_count":  0,
        "last_output": None,
    }
    return {
        "session_id":   session_id,
        "domain":       body.domain,
        "fs":           body.fs,
        "engine_build": BUILD_TAG,
        "push_url":     f"/trial/session/{session_id}/push",
        "status_url":   f"/trial/session/{session_id}/status",
        "note": (
            "POST waveform windows (JSON) to push_url — manual entry or "
            "sensor-driven. Poll status_url for live updates."
        ),
    }


class TrialPushRequest(BaseModel):
    trial_code: Optional[str] = Field(
        None,
        description="Trial code. Can also be supplied via X-Trial-Code header instead of body.")
    waveform:   List[float] = Field(..., min_length=16, max_length=20000,
                                    description="Signal samples, normalized to [-1, 1].")
    magnitudes: Optional[List[float]] = None
    mc:         float = 0.0
    timestamp:  Optional[float] = None

    @field_validator("magnitudes")
    @classmethod
    def _check_mags(cls, v):
        if v is not None and len(v) < 5:
            raise ValueError("magnitudes must contain at least 5 values.")
        return v


@app.post("/trial/session/{session_id}/push")
def trial_session_push(
    session_id: str,
    body: TrialPushRequest,
    request: Request,
    x_trial_code: Optional[str] = Header(None, alias="X-Trial-Code"),
):
    """
    Push a waveform window to an active trial session.
    Accepts real buyer waveform data — no synthetic profiles used.
    Auth: X-Trial-Code header (preferred) or trial_code in JSON body.
    trial_code never appears in the URL — not logged in server access logs.
    """
    _check_trial_rate(request)
    _check_trial_code(x_trial_code or body.trial_code or "")
    _expire_trial_sessions()

    if session_id not in _TRIAL_SESSIONS:
        raise HTTPException(status_code=404, detail="Trial session not found or expired.")

    sess   = _TRIAL_SESSIONS[session_id]
    engine: TCEngine = sess["engine"]

    waveform = np.array(body.waveform, dtype=float)
    _check_normalized(waveform)
    mags = np.array(body.magnitudes) if body.magnitudes else None

    try:
        out = engine.analyse(waveform=waveform, magnitudes=mags,
                             mc=body.mc, timestamp=body.timestamp)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    sess["last_active"] = time.time()
    sess["push_count"] += 1
    sess["last_output"] = out

    response = _build_response(out, mode="session")
    response["session_id"] = session_id
    response["push_count"] = sess["push_count"]
    return response


@app.get("/trial/session/{session_id}/status")
def trial_session_status(
    session_id: str,
    request: Request,
    x_trial_code: str = Header(..., alias="X-Trial-Code"),
):
    _check_trial_rate(request)
    _check_trial_code(x_trial_code)
    _expire_trial_sessions()

    if session_id not in _TRIAL_SESSIONS:
        raise HTTPException(status_code=404, detail="Trial session not found or expired.")

    sess = _TRIAL_SESSIONS[session_id]
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
        base["note"] = "No data pushed yet."
    return base


@app.delete("/trial/session/{session_id}")
def trial_session_delete(
    session_id: str,
    x_trial_code: str = Header(..., alias="X-Trial-Code"),
):
    _check_trial_code(x_trial_code)
    if session_id not in _TRIAL_SESSIONS:
        raise HTTPException(status_code=404, detail="Trial session not found or expired.")
    del _TRIAL_SESSIONS[session_id]
    return {"session_id": session_id, "status": "terminated"}


@app.post("/trial/csv/{domain}")
def trial_csv(domain: str, request: Request,
              file:       UploadFile = File(...),
              trial_code: str        = Form(...),
              mc:         float      = Form(0.0),
              fs:         float      = Form(100.0)):
    """
    CSV waveform upload — trial-code gated screening analysis (no persistence).
    Auth: trial_code as multipart form field — never in the URL or query string.

    CSV format notes:
      - Single-column preferred: one sample per row.
      - Multi-column CSVs are accepted and flattened row-major before analysis.
        This is intentional — useful for exporting rows from data loggers.
      - All non-finite values (NaN, Inf) are silently dropped before analysis.
      - Waveform must be pre-normalized to [-1, 1] before upload.
    """
    _check_trial_rate(request)
    _check_trial_code(trial_code)

    try:
        get_domain_config(domain)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if fs <= 0 or fs > 100_000:
        raise HTTPException(status_code=422, detail="fs must be between 0 and 100000 Hz.")
    if not -10 <= mc <= 10:
        raise HTTPException(status_code=422, detail="mc must be between -10 and 10.")

    try:
        contents = file.file.read()
        if len(contents) > 2_000_000:
            raise HTTPException(status_code=413, detail="CSV file too large. Maximum 2 MB.")
        data = np.genfromtxt(io.BytesIO(contents), delimiter=",")
        data = data.flatten()
        data = data[np.isfinite(data)]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {e}")

    if len(data) < 16:
        raise HTTPException(status_code=422, detail="CSV must contain at least 16 finite values.")
    _check_normalized(data)

    engine = TCEngine(domain=domain, fs=fs, enable_surrogate_gate=False)
    try:
        out = engine.analyse(waveform=data, mc=mc, apply_surrogate_gate=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _build_response(out, mode="screening")


# ── Public verification harness ───────────────────────────────────────────────
# Shows buyers how the engine responds to modeled precursor profiles
# based on documented historical event characteristics.
# Rate-limited per IP — same limiter as the rest of the public demo surface.
# Function name retained as demo_validate_all for API stability.

PUBLIC_DEMO_DISCLAIMER = (
    "Public demonstration output. Results are generated by a controlled "
    "simulation harness using synthetic precursor profiles modeled on "
    "documented characteristics of major historical events, including "
    "Tohoku 2011, Eyjafjallajokull 2010, and Rana Plaza 2013. "
    "Independent retrospective validation against raw instrument data "
    "is pending under TC-VAL-PROTO-001. These outputs demonstrate "
    "engine response behavior and decision logic; they are not certified "
    "historical reproductions or operational predictions."
)

API_VERSION    = "3.2.0"
SCHEMA_VERSION = "1.0"


class ValidationSummary(BaseModel):
    passed: int
    failed: int
    total:  int


class ValidationDemoResponse(BaseModel):
    request_id:      str
    generated_at:    str
    api_version:     str
    engine_build:    str
    schema_version:  str
    validation_type: str
    access_level:    str
    result_count:    int
    execution_ms:    float
    summary:         ValidationSummary
    results:         Dict[str, Any]
    disclaimer:      str


class ErrorResponse(BaseModel):
    request_id:   str
    generated_at: str
    error:        str
    detail:       str
    api_version:  str
    engine_build: str


@app.post(
    "/demo/validate/all",
    response_model=ValidationDemoResponse,
    responses={
        200: {"description": "Verification harness completed successfully."},
        429: {"description": "Rate limit reached. Try again shortly."},
        500: {
            "model":       ErrorResponse,
            "description": "Internal engine error. Reference request_id when contacting support.",
        },
    },
)
def demo_validate_all(request: Request, response: Response):
    _check_demo_rate(request)

    response.headers["Cache-Control"] = "no-store"

    request_id   = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Fields safe to expose publicly — explicitly allowlisted.
    # Any new fields added to run_validation() output in tc_engine_v3
    # are suppressed until reviewed and added to this list.
    # Explicit public allowlist — any field added to run_validation() in future
    # tc_engine_v3 versions is suppressed until reviewed and added here.
    # "channels" is included: run_validation() already calls
    # sanitize_channel_for_api() on each channel, which strips weights,
    # thresholds, and internal formulas — only score/label/safe metadata exposed.
    _PUBLIC_VALIDATION_FIELDS = frozenset({
        "description", "domain", "cci_peak", "alert_level", "raw_alert_level",
        "first_warning_window", "lead_time_windows", "total_windows",
        "noise_floor_mean_cci", "noise_floor_std_cci", "z_score_vs_noise_floor",
        "noise_floor_note", "persistence_score", "confidence", "status",
        "audit_hash", "disclaimer",
        # "channels" kept — already sanitized via sanitize_channel_for_api()
        # in tc_engine_v3.run_validation(). Remove if that changes.
        "channels",
    })

    def _sanitize_validation_result(r: dict) -> dict:
        """Strip any fields not in the public allowlist before returning to buyers."""
        return {k: v for k, v in r.items() if k in _PUBLIC_VALIDATION_FIELDS}

    try:
        start      = time.perf_counter()
        raw        = run_validation()
        results    = {k: _sanitize_validation_result(v) for k, v in raw.items()}
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    except Exception as exc:
        logger.exception("Verification harness failed: request_id=%s", request_id)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "request_id":   request_id,
                "generated_at": generated_at,
                "error":        "Verification harness failed.",
                "detail":       "Internal validation error. Reference request_id when contacting support.",
                "api_version":  API_VERSION,
                "engine_build": BUILD_TAG,
            },
        )

    passed = sum(1 for r in results.values() if r.get("status") == "SIM-HARNESS-PASS")
    failed = len(results) - passed

    return {
        "request_id":      request_id,
        "generated_at":    generated_at,
        "api_version":     API_VERSION,
        "engine_build":    BUILD_TAG,
        "schema_version":  SCHEMA_VERSION,
        "validation_type": "public_simulation_harness",
        "access_level":    "demo_public",
        "result_count":    len(results),
        "execution_ms":    elapsed_ms,
        "summary": {
            "passed": passed,
            "failed": failed,
            "total":  len(results),
        },
        "results":    results,
        "disclaimer": PUBLIC_DEMO_DISCLAIMER,
    }
