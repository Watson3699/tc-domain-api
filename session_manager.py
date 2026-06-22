"""
TC Session Manager
==================
AW IP Holdings Inc. | CONFIDENTIAL

Manages persistent TCEngine instances for streaming / continuous monitoring.

Each session holds a live engine per domain. Kalman and Ljung-Box history
accumulate across push() calls — this is the correct operational mode for
seismic and volcanic continuous monitoring.

Storage: in-memory dict. Sessions survive as long as the server process is
running. Render starter plan restarts periodically — sessions do not survive
restarts. For production persistence, replace _sessions with a Redis-backed
store (see TODO-REDIS comment below).

Session expiry: 24 hours of inactivity. Cleaned up lazily on create/push.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import numpy as np

from tc_engine_v2 import TCEngine, EngineOutput
from domain_config import DOMAINS

# ── CONFIG ────────────────────────────────────────────────────────────────────

SESSION_TTL_SECONDS     = 86400    # 24h inactivity before expiry
MAX_SESSIONS            = 200      # hard cap — prevents memory exhaustion
MAX_WINDOWS_PER_SESSION = 10_000   # safety ceiling per session


# ── SESSION RECORD ────────────────────────────────────────────────────────────

@dataclass
class Session:
    session_id:   str
    domain:       str
    engine:       TCEngine
    created_at:   float = field(default_factory=time.time)
    last_active:  float = field(default_factory=time.time)
    window_count: int   = 0
    peak_cci:     float = 0.0
    peak_alert:   str   = "NOMINAL"
    last_cci:     float = 0.0
    last_alert:   str   = "NOMINAL"
    last_hash:    str   = ""

    def touch(self) -> None:
        self.last_active = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TTL_SECONDS

    def to_status_dict(self) -> dict:
        return {
            "session_id":   self.session_id,
            "domain":       self.domain,
            "window_count": self.window_count,
            "peak_cci":     round(self.peak_cci, 4),
            "peak_alert":   self.peak_alert,
            "last_cci":     round(self.last_cci, 4),
            "last_alert":   self.last_alert,
            "last_hash":    self.last_hash,
            "created_at":   self.created_at,
            "last_active":  self.last_active,
            "age_minutes":  round((time.time() - self.created_at) / 60, 1),
            "idle_minutes": round((time.time() - self.last_active) / 60, 1),
        }


# ── SESSION STORE ─────────────────────────────────────────────────────────────
# TODO-REDIS: replace _sessions dict with a Redis client for production.
# Key: session_id  |  Value: serialised Session + engine state checkpoint
# Enables session survival across Render restarts and horizontal scaling.

_sessions: Dict[str, Session] = {}


# ── EXCEPTIONS ────────────────────────────────────────────────────────────────

class SessionError(Exception):           pass
class SessionNotFound(SessionError):     pass
class SessionLimitReached(SessionError): pass
class SessionWindowLimit(SessionError):  pass


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _purge_expired() -> None:
    expired = [sid for sid, s in _sessions.items() if s.is_expired()]
    for sid in expired:
        del _sessions[sid]


# ── PUBLIC INTERFACE ──────────────────────────────────────────────────────────

def create_session(domain: str) -> Session:
    """Create a new monitoring session. Returns Session with session_id."""
    if domain not in DOMAINS:
        raise SessionError(f"Unknown domain '{domain}'. Must be one of: {DOMAINS}")
    _purge_expired()
    if len(_sessions) >= MAX_SESSIONS:
        raise SessionLimitReached(
            f"Maximum concurrent sessions ({MAX_SESSIONS}) reached. "
            "Delete an existing session or wait for expiry (24h)."
        )
    sid     = str(uuid.uuid4())
    session = Session(session_id=sid, domain=domain, engine=TCEngine())
    _sessions[sid] = session
    return session


def get_session(session_id: str) -> Session:
    """Retrieve active session. Raises SessionNotFound if missing or expired."""
    s = _sessions.get(session_id)
    if s is None:
        raise SessionNotFound(f"Session '{session_id}' not found.")
    if s.is_expired():
        del _sessions[session_id]
        raise SessionNotFound(
            f"Session '{session_id}' expired after 24h inactivity. Create a new session."
        )
    return s


def push_window(
    session_id: str,
    waveform:   np.ndarray,
    magnitudes: Optional[np.ndarray] = None,
    mc:         float = 0.0,
) -> Tuple[Session, EngineOutput]:
    """
    Submit next window to session engine. State accumulates across calls.
    This is the core streaming operation — Kalman and LB history build
    with each push, making CCI increasingly meaningful over time.
    """
    _purge_expired()
    session = get_session(session_id)

    if session.window_count >= MAX_WINDOWS_PER_SESSION:
        raise SessionWindowLimit(
            f"Session has reached {MAX_WINDOWS_PER_SESSION} windows. "
            "Create a new session to continue."
        )

    result = session.engine.analyse(
        waveform=waveform,
        magnitudes=magnitudes,
        mc=mc,
    )

    session.window_count += 1
    session.last_cci      = result.cci
    session.last_alert    = result.alert_level
    session.last_hash     = result.audit_hash

    if result.cci > session.peak_cci:
        session.peak_cci   = result.cci
        session.peak_alert = result.alert_level

    session.touch()
    return session, result


def delete_session(session_id: str) -> bool:
    """Remove session. Returns True if found and deleted."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def active_session_count() -> int:
    return len(_sessions)

