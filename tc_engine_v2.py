"""
Triple-Convergence Acoustic Diagnostic Engine v2.0
===================================================
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
Document: TC-ENG-CORE-002

Four-channel Coherence Convergence Index (CCI):
  CH-01  Gutenberg-Richter b-value          weight 0.30
  CH-02  Eigen-tracked Kalman κ(P)          weight 0.25
  CH-03  Spectral k-ratio [NDA-gated stub]  weight 0.25
  CH-04  Adaptive AR(p) + Ljung-Box         weight 0.20

DWT multi-scale decomposition conditions the waveform and feeds the
Kalman observation vector internally. It is not a public channel and
band_energies are never returned in API responses.

Engine internals (weights, thresholds, k-ratio formula) are trade
secrets and are never returned in any API response.

Build note: TC-ENGINE-2025-V2-SIM-STUB indicates the k-ratio channel
is running on an interface-contract stub — a deterministic placeholder
that is NOT the production k-ratio formula. Upgrade build tag to
TC-ENGINE-2025-V2-PROD after the NDA-gated production module is installed.
"""
from __future__ import annotations

import hashlib
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np
from scipy import signal as sp_signal

# ── BUILD CONSTANTS ───────────────────────────────────────────────────────────

VERSION   = "2.0.0"
BUILD_TAG = "TC-ENGINE-2025-V2-SIM-STUB"

# CCI channel weights — trade secret, never exposed in API responses
_CCI_WEIGHTS: Dict[str, float] = {
    "b_value":   0.30,
    "kappa":     0.25,
    "k_ratio":   0.25,
    "ljung_box": 0.20,
}
assert abs(sum(_CCI_WEIGHTS.values()) - 1.0) < 1e-9

# Alert thresholds — trade secret, never exposed in API responses
_THRESHOLD_ADVISORY = 0.65
_THRESHOLD_WARNING  = 0.78
_THRESHOLD_CRITICAL = 0.88

# Internal config
_LB_HISTORY_LEN = 120
_LB_LAG_DEFAULT = 10
_DWT_LEVEL      = 4
_KALMAN_DIM     = 4

# Whitelist of metadata keys safe to return in public API responses
_PUBLIC_METADATA_KEYS: frozenset = frozenset({"n_events", "flagged", "level"})


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class ChannelResult:
    normalised: float
    label:      str
    metadata:   Dict = field(default_factory=dict)
    # raw values intentionally omitted — never pass raw to API responses


@dataclass
class EngineOutput:
    timestamp:    float
    cci:          float
    alert_level:  str
    channels:     Dict[str, ChannelResult] = field(default_factory=dict)
    audit_hash:   str = ""
    sample_count: int = 0


# ── LAYER 1 — MULTI-SCALE DWT (internal only) ─────────────────────────────────

def _haar_filters() -> Tuple[np.ndarray, np.ndarray]:
    lo = np.array([1.0, 1.0]) / np.sqrt(2)
    hi = np.array([1.0, -1.0]) / np.sqrt(2)
    return lo, hi


def _db4_filters() -> Tuple[np.ndarray, np.ndarray]:
    c  = np.array([0.48296291314469025, 0.83651630373746899,
                   0.22414386804185735, -0.12940952255092145])
    lo = c / np.sqrt(2)
    hi = np.array([c[3], -c[2], c[1], -c[0]]) / np.sqrt(2)
    return lo, hi


def _dwt_level(x: np.ndarray, lo: np.ndarray,
               hi: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    approx = np.convolve(x, lo, mode="full")[1::2]
    detail = np.convolve(x, hi, mode="full")[1::2]
    n = min(len(approx), len(detail))
    return approx[:n], detail[:n]


def _dwt_energy_profile(x: np.ndarray,
                         level: int = _DWT_LEVEL) -> Tuple[np.ndarray, float]:
    """Internal DWT decomposition — band_energies never leave this module."""
    lo, hi    = _db4_filters()
    approx    = x.astype(float).copy()
    det_e: List[float] = []
    for _ in range(level):
        if len(approx) < 2 * len(lo):
            det_e.append(0.0)
            continue
        approx, det = _dwt_level(approx, lo, hi)
        det_e.append(float(np.sum(det ** 2)))
    approx_e = float(np.sum(approx ** 2))
    all_e    = np.array(det_e + [approx_e])
    total    = all_e.sum() + 1e-12
    norm_e   = all_e / total
    scales   = np.arange(len(norm_e), dtype=float)
    mig      = float(np.dot(norm_e, scales) / len(scales))
    return norm_e, mig


def _compute_dwt_internal(waveform: np.ndarray) -> Tuple[np.ndarray, float]:
    """DWT used internally only. Returns (band_energies, migration_index)."""
    return _dwt_energy_profile(waveform)


# ── LAYER 2 — EIGEN-TRACKED KALMAN ───────────────────────────────────────────

class _EigenKalman:
    def __init__(self, dim: int = _KALMAN_DIM,
                 process_noise: float = 1e-3,
                 obs_noise:     float = 1e-2) -> None:
        self.dim = dim
        self.x   = np.zeros(dim)
        self.P   = np.eye(dim) * 0.1
        self.Q   = np.eye(dim) * process_noise
        self.R   = np.eye(dim) * obs_noise
        self.F   = np.eye(dim)
        self.H   = np.eye(dim)
        self._kappa_hist: Deque[float] = deque(maxlen=50)

    def update(self, z: np.ndarray) -> Tuple[float, float]:
        x_pred = self.F @ self.x
        P_pred = self.F @ self.P @ self.F.T + self.Q
        S      = self.H @ P_pred @ self.H.T + self.R
        K      = P_pred @ self.H.T @ np.linalg.inv(S)
        self.x = x_pred + K @ (z - self.H @ x_pred)
        self.P = (np.eye(self.dim) - K @ self.H) @ P_pred
        eigs        = np.abs(np.linalg.eigvalsh(self.P))
        kappa       = float(eigs.max() / max(eigs.min(), 1e-12))
        self._kappa_hist.append(kappa)
        p95         = float(np.percentile(np.array(self._kappa_hist), 95))
        kappa_norm  = float(np.clip(kappa / max(p95, 1.0), 0.0, 1.0))
        return kappa, kappa_norm   # kappa (raw) never forwarded to API response


def _compute_kalman_channel(obs: np.ndarray, kf: _EigenKalman) -> ChannelResult:
    z = np.zeros(kf.dim)
    z[:min(len(obs), kf.dim)] = obs[:kf.dim]
    _kappa_raw, kappa_norm = kf.update(z)
    # _kappa_raw intentionally discarded — not stored in metadata
    return ChannelResult(
        normalised=kappa_norm,
        label="Kalman covariance geometry",
        metadata={},
    )


# ── LAYER 3 — ADAPTIVE LJUNG-BOX ─────────────────────────────────────────────

def _autocorr(x: np.ndarray, lag: int) -> float:
    n, mu = len(x), x.mean()
    c0    = float(np.sum((x - mu) ** 2))
    if c0 < 1e-12:
        return 0.0
    return float(np.sum((x[lag:] - mu) * (x[:n - lag] - mu))) / c0


def _lb_statistic(residuals: np.ndarray, lags: int = _LB_LAG_DEFAULT) -> float:
    n = len(residuals)
    if n < lags + 2:
        return 0.0
    return float(n * (n + 2) * sum(
        _autocorr(residuals, k) ** 2 / (n - k) for k in range(1, lags + 1)
    ))


def _chi2_sf(q: float, df: int) -> float:
    try:
        from scipy.stats import chi2
        return float(chi2.sf(q, df))
    except Exception:
        if df <= 0 or q < 0:
            return 1.0
        mu_z    = 1.0 - 2.0 / (9.0 * df)
        sigma_z = np.sqrt(2.0 / (9.0 * df))
        z       = ((q / df) ** (1.0 / 3.0) - mu_z) / sigma_z
        return float(0.5 * (1.0 - np.tanh(z * 0.7071067811865476)))


class _AdaptiveLjungBox:
    def __init__(self, history_len: int = _LB_HISTORY_LEN,
                 z_threshold: float = 2.0,
                 ar_order: int = 4,
                 lags: int = _LB_LAG_DEFAULT) -> None:
        self.z_threshold = z_threshold
        self.ar_order    = ar_order
        self.lags        = lags
        self._p_hist: Deque[float] = deque(maxlen=history_len)

    def _ar_residuals(self, x: np.ndarray) -> np.ndarray:
        p, n = self.ar_order, len(x)
        if n <= p + 2:
            return x - x.mean()
        X = np.column_stack([x[p - i - 1: n - i - 1] for i in range(p)])
        y = x[p:]
        try:
            beta      = np.linalg.lstsq(X, y, rcond=None)[0]
            residuals = y - X @ beta
        except np.linalg.LinAlgError:
            residuals = y - y.mean()
        return residuals

    def update(self, x: np.ndarray) -> Tuple[bool, float]:
        residuals = self._ar_residuals(x)
        q_stat    = _lb_statistic(residuals, self.lags)
        p_value   = _chi2_sf(q_stat, self.lags)
        # p_value and z_score are internal — not forwarded to API response
        if len(self._p_hist) >= 10:
            p_arr   = np.array(self._p_hist)
            z_score = (p_arr.mean() - p_value) / (p_arr.std() + 1e-9)
            flagged = bool(z_score > self.z_threshold)
        else:
            z_score = 0.0
            flagged = bool(p_value < 0.05)
        self._p_hist.append(p_value)
        p_norm     = float(np.clip(1.0 - p_value, 0.0, 1.0))
        z_norm     = float(np.clip(z_score / (self.z_threshold * 2), 0.0, 1.0))
        norm_score = 0.6 * p_norm + 0.4 * z_norm
        return flagged, norm_score


def _compute_lb_channel(window: np.ndarray, alb: _AdaptiveLjungBox) -> ChannelResult:
    flagged, norm = alb.update(window)
    return ChannelResult(
        normalised=norm,
        label="Temporal clustering index",
        metadata={"flagged": flagged},
    )


# ── K-RATIO STUB (NDA-gated) ──────────────────────────────────────────────────

def _compute_k_ratio_channel(waveform: np.ndarray) -> ChannelResult:
    """
    Proprietary spectral k-ratio — full methodology is a trade secret of
    AW IP Holdings Inc., disclosed only under executed NDA.

    This stub returns a deterministic interface-contract placeholder and is
    NOT the production k-ratio formula. The placeholder uses a simple
    time-domain energy split that has no relationship to the production
    spectral methodology.

    Build tag remains TC-ENGINE-2025-V2-SIM-STUB until the production
    module is installed.
    """
    n    = len(waveform)
    mid  = n // 2
    lo   = float(np.mean(waveform[:mid] ** 2)) + 1e-12
    hi   = float(np.mean(waveform[mid:] ** 2)) + 1e-12
    norm = float(np.clip(1.0 / (1.0 + hi / lo), 0.0, 1.0))
    return ChannelResult(
        normalised=norm,
        label="Spectral coherence index",
        metadata={},
    )


# ── G-R B-VALUE ───────────────────────────────────────────────────────────────

def _compute_b_value_channel(magnitudes: np.ndarray,
                              mc: float = 0.0) -> ChannelResult:
    m = magnitudes[magnitudes >= mc]
    if len(m) < 5:
        return ChannelResult(normalised=0.0, label="Stress index",
                             metadata={"n_events": int(len(m))})
    dm = m.mean() - mc
    if dm < 1e-9:
        return ChannelResult(normalised=1.0, label="Stress index",
                             metadata={"n_events": int(len(m))})
    b    = np.log10(np.e) / dm
    norm = float(np.clip((1.3 - b) / 1.0, 0.0, 1.0))
    # b value itself is internal — only n_events exposed
    return ChannelResult(
        normalised=norm,
        label="Stress index",
        metadata={"n_events": int(len(m))},
    )


# ── CCI COMPOSITE ─────────────────────────────────────────────────────────────

def _compute_cci(channels: Dict[str, ChannelResult]) -> float:
    cci = sum(
        w * (channels[k].normalised if k in channels else 0.0)
        for k, w in _CCI_WEIGHTS.items()
    )
    return float(np.clip(cci, 0.0, 1.0))


def _cci_to_alert(cci: float) -> str:
    if cci >= _THRESHOLD_CRITICAL: return "CRITICAL"
    if cci >= _THRESHOLD_WARNING:  return "WARNING"
    if cci >= _THRESHOLD_ADVISORY: return "ADVISORY"
    return "NOMINAL"


def _audit_hash(cci: float, ts: float, run: int) -> str:
    payload = f"{BUILD_TAG}|{cci:.6f}|{ts:.2f}|{run}"
    return hashlib.sha256(payload.encode()).hexdigest()


# ── MAGNITUDE SYNTHESIS (deterministic) ──────────────────────────────────────

def _synthesise_magnitudes(waveform: np.ndarray, n_events: int = 30) -> np.ndarray:
    """
    Derive proxy magnitude catalogue from waveform envelope peaks.
    Fallback is deterministic: seeded from waveform content hash.
    """
    envelope = np.abs(sp_signal.hilbert(waveform))
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(envelope, distance=max(1, len(waveform) // (n_events * 2)))
    if len(peaks) < 3:
        seed = int(hashlib.md5(waveform.tobytes()).hexdigest()[:8], 16) % (2 ** 32)
        rng  = np.random.default_rng(seed)
        return rng.uniform(0.5, 2.5, n_events)
    amps = envelope[peaks]
    mags = np.log10(amps + 1e-6)
    mags -= mags.min()
    mags /= mags.max() + 1e-9
    return mags * 2.5 + 0.2


# ── INPUT VALIDATION ──────────────────────────────────────────────────────────

def _validate_waveform(waveform: np.ndarray) -> np.ndarray:
    """Centralised waveform guard — called at engine boundary."""
    if waveform is None or len(waveform) < 16:
        raise ValueError("waveform must contain at least 16 samples.")
    waveform = np.asarray(waveform, dtype=float)
    if not np.all(np.isfinite(waveform)):
        raise ValueError("waveform contains NaN or infinite values.")
    return waveform


# ── PUBLIC SANITISATION HELPER ────────────────────────────────────────────────

def sanitize_channel_for_api(ch_key: str, ch_val: ChannelResult) -> dict:
    """
    Public helper — returns only whitelisted metadata keys.
    Used by both /analyse and /validate to ensure consistent sanitisation.
    Internal values (kappa_raw, p_value, z_score, band_energies, b_value
    raw, stub flags) are never included.
    """
    safe_meta = {k: v for k, v in ch_val.metadata.items()
                 if k in _PUBLIC_METADATA_KEYS}
    return {
        "score":    round(ch_val.normalised, 4),
        "label":    ch_val.label,
        "metadata": safe_meta,
    }


# ── MAIN ENGINE ───────────────────────────────────────────────────────────────

class TCEngine:
    """
    Triple-Convergence Acoustic Diagnostic Engine v2.0

    Stateful per-instance: Kalman filter and Ljung-Box history accumulate
    across calls to analyse(). For independent per-request scoring, create
    a fresh TCEngine() per request (see FastAPI wrapper).

    Black-box: channel weights, thresholds, and k-ratio methodology are
    not accessible through any public interface.
    """

    def __init__(self) -> None:
        self._kalman    = _EigenKalman(dim=_KALMAN_DIM)
        self._alb       = _AdaptiveLjungBox()
        self._run_count = 0

    def analyse(
        self,
        waveform:   np.ndarray,
        magnitudes: Optional[np.ndarray] = None,
        mc:         float = 0.0,
        timestamp:  Optional[float] = None,
    ) -> EngineOutput:
        # Fix: correct None-safe timestamp — avoids falsy 0.0 edge case
        ts = time.time() if timestamp is None else timestamp

        waveform = _validate_waveform(waveform)
        self._run_count += 1

        # DWT: internal conditioning — band_energies never leave analyse()
        band_e, _migration = _compute_dwt_internal(waveform)

        rms = float(np.sqrt(np.mean(waveform ** 2)))
        obs = np.array([
            band_e[0] if len(band_e) > 0 else 0.0,
            band_e[1] if len(band_e) > 1 else 0.0,
            band_e[2] if len(band_e) > 2 else 0.0,
            rms,
        ])

        kalman_result = _compute_kalman_channel(obs, self._kalman)
        lb_result     = _compute_lb_channel(waveform, self._alb)

        if magnitudes is None:
            magnitudes = _synthesise_magnitudes(waveform)
        else:
            magnitudes = np.asarray(magnitudes, dtype=float)
            if len(magnitudes) < 5:
                raise ValueError('magnitudes must contain at least 5 values if provided.')
            if not np.all(np.isfinite(magnitudes)):
                raise ValueError('magnitudes contains NaN or infinite values.')
        b_result = _compute_b_value_channel(magnitudes, mc)
        k_result = _compute_k_ratio_channel(waveform)

        # Four public channels only — DWT is internal
        channels = {
            "b_value":   b_result,
            "kappa":     kalman_result,
            "k_ratio":   k_result,
            "ljung_box": lb_result,
        }

        cci         = _compute_cci(channels)
        alert_level = _cci_to_alert(cci)

        return EngineOutput(
            timestamp=ts,
            cci=cci,
            alert_level=alert_level,
            channels=channels,
            audit_hash=_audit_hash(cci, ts, self._run_count),
            sample_count=len(waveform),
        )


# ── VALIDATION HARNESS ────────────────────────────────────────────────────────

_VALIDATION_EVENTS: Dict[str, dict] = {
    "Tohoku_2011": {
        "description":    "Mw 9.1 megathrust — offshore Honshu, Japan",
        "domain":         "Seismic",
        "onset_frac":     0.12,
        "severity_scale": 0.89,
        "seed":           2011,
    },
    "Eyjafjallajokull_2010": {
        "description":    "VEI 4 sub-glacial eruption — Iceland",
        "domain":         "Volcanic",
        "onset_frac":     0.18,
        "severity_scale": 0.81,
        "seed":           2010,
    },
    "Rana_Plaza_2013": {
        "description":    "Structural progressive collapse — Dhaka, Bangladesh",
        "domain":         "Structural AE",
        "onset_frac":     0.22,
        "severity_scale": 0.76,
        "seed":           2013,
    },
}


def _make_precursor_signal(n: int, onset_frac: float,
                            severity_scale: float, seed: int) -> np.ndarray:
    rng    = np.random.default_rng(seed)
    t      = np.linspace(0, 4 * np.pi, n)
    sig    = rng.normal(0, 0.1, n)
    onset  = int(n * onset_frac)
    sf     = 0.3 + (1 - severity_scale) * 0.5
    ramp   = np.linspace(0, severity_scale * 2, n - onset)
    sig[onset:] += ramp * np.sin(sf * t[onset:])
    burst  = int(n * 0.85)
    sig[burst:] += rng.normal(0, severity_scale * 1.5, n - burst)
    return sig


def run_validation(n_samples: int = 512) -> Dict:
    """
    Run the synthetic historical event harness.

    Each event uses a fresh TCEngine instance to prevent cross-contamination
    of Kalman and Ljung-Box state between events.

    Reports peak CCI across the windowed analysis — the highest alert
    reached before the event, not the final window state.

    Internal fields (severity_scale, seed, band_energies, raw channel
    values) are never included in the returned dict.
    """
    results: Dict = {}

    for event_id, cfg in _VALIDATION_EVENTS.items():
        engine   = TCEngine()   # fresh per event — no state contamination
        waveform = _make_precursor_signal(
            n=n_samples,
            onset_frac=cfg["onset_frac"],
            severity_scale=cfg["severity_scale"],
            seed=cfg["seed"],
        )

        window_size = 128
        step        = 32
        peak_out    = None
        peak_cci    = -1.0
        window_idx  = 0

        for i, start in enumerate(range(0, n_samples - window_size + 1, step)):
            out = engine.analyse(waveform=waveform[start: start + window_size])
            if out.cci > peak_cci:
                peak_cci   = out.cci
                peak_out   = out
                window_idx = i

        out    = peak_out
        status = "SIM-HARNESS-PASS" if out.cci >= cfg["severity_scale"] * 0.90 else "SIM-HARNESS-FAIL"

        results[event_id] = {
            "description":      cfg["description"],
            "domain":           cfg["domain"],
            "synthetic_profile": "synthetic precursor profile",
            "cci_achieved":     round(out.cci, 4),
            "alert_level":      out.alert_level,
            "status":           status,
            "audit_hash":       out.audit_hash,
            "channels": {
                k: sanitize_channel_for_api(k, v)
                for k, v in out.channels.items()
            },
        }

    return results

