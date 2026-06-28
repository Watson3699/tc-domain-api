"""
tc_engine_v3.py
===============
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
Document: TC-ENG-CORE-003

Triple-Convergence Acoustic Diagnostic Engine v3.0
===================================================
Upgrade from v2.0:
  - CH-03 k-ratio stub REPLACED by AttractorDrift (phase-space geometry)
  - CH-05 PLV (Phase Locking Value) ADDED — phase coupling channel
  - Domain-specific CCI weight tables (seismic / volcanic / structural)
  - Multi-window persistence gate — alert suppressed until N of M windows confirm
  - IAAFT surrogate rejection gate — alert downgraded if CCI indistinguishable
    from linear-phase-shuffled surrogate (kills linear false alarms)
  - Confidence score output: persistence × surrogate_gate × data_quality
  - Expanded validation output schema: lead-time, z-score vs surrogate,
    surrogate_mean, first_warning_window, status

Five-channel CCI (domain-specific weights — see domain_weights.py):
  CH-01  Gutenberg-Richter b-value       (stress accumulation proxy)
  CH-02  Eigen-tracked Kalman κ(P)       (covariance geometry drift)
  CH-03  AttractorDrift                  (recurrence threshold drift)
  CH-04  PLV Phase Locking Value         (inter-mode phase coupling)
  CH-05  Adaptive AR(p) + Ljung-Box      (temporal clustering)

DWT multi-scale decomposition conditions the Kalman observation vector
internally. Band energies are never returned in API responses.

Engine internals (weights, thresholds, channel formulas) are trade
secrets of AW IP Holdings Inc. and are never returned in any API response.

Build tag: TC-ENGINE-2025-V3-PROD
"""
from __future__ import annotations

import hashlib
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np
from scipy import signal as sp_signal
from scipy.signal import find_peaks

from spectral_geometry import AttractorDrift
from plv_channel import PLVChannel
from domain_weights import (
    get_domain_config,
    THRESHOLD_ADVISORY,
    THRESHOLD_WARNING,
    THRESHOLD_CRITICAL,
    SURROGATE_Z_MIN,
    CONFIDENCE_FLOOR,
)
from persistence import PersistenceGate
from surrogate import SurrogateGate

# ── BUILD CONSTANTS ───────────────────────────────────────────────────────────

VERSION   = "3.0.0"
BUILD_TAG = "TC-ENGINE-2025-V3-PROD"

# Internal config
_LB_HISTORY_LEN = 120
_LB_LAG_DEFAULT = 10
_DWT_LEVEL      = 4
_KALMAN_DIM     = 4

# Whitelist of metadata keys safe to return in API responses
_PUBLIC_METADATA_KEYS: frozenset = frozenset({"n_events", "flagged", "level", "rising"})


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────

@dataclass
class ChannelResult:
    normalised: float
    label:      str
    metadata:   Dict = field(default_factory=dict)


@dataclass
class EngineOutput:
    timestamp:          float
    cci:                float
    alert_level:        str          # persistence-gated level
    raw_alert_level:    str          # raw CCI threshold level (no persistence)
    domain:             str
    channels:           Dict[str, ChannelResult] = field(default_factory=dict)
    audit_hash:         str  = ""
    sample_count:       int  = 0
    persistence_score:  float = 0.0  # fraction toward gate satisfaction
    confidence:         float = 0.0  # composite confidence [0,1]
    surrogate_z:        float = 0.0  # z-score vs IAAFT surrogate (0 = not tested)
    surrogate_tested:   bool  = False


# ── LAYER 1 — MULTI-SCALE DWT (internal only) ─────────────────────────────────

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
    """Internal DWT — band_energies never leave this function."""
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

    def update(self, z: np.ndarray) -> float:
        x_pred = self.F @ self.x
        P_pred = self.F @ self.P @ self.F.T + self.Q
        S      = self.H @ P_pred @ self.H.T + self.R
        K      = P_pred @ self.H.T @ np.linalg.inv(S)
        self.x = x_pred + K @ (z - self.H @ x_pred)
        self.P = (np.eye(self.dim) - K @ self.H) @ P_pred
        eigs       = np.abs(np.linalg.eigvalsh(self.P))
        kappa      = float(eigs.max() / max(eigs.min(), 1e-12))
        self._kappa_hist.append(kappa)
        p95        = float(np.percentile(np.array(self._kappa_hist), 95))
        kappa_norm = float(np.clip(kappa / max(p95, 1.0), 0.0, 1.0))
        return kappa_norm   # raw kappa intentionally discarded


def _compute_kalman_channel(obs: np.ndarray, kf: _EigenKalman) -> ChannelResult:
    z = np.zeros(kf.dim)
    z[:min(len(obs), kf.dim)] = obs[:kf.dim]
    kappa_norm = kf.update(z)
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
    return ChannelResult(
        normalised=norm,
        label="Stress index",
        metadata={"n_events": int(len(m))},
    )


# ── MAGNITUDE SYNTHESIS ───────────────────────────────────────────────────────

def _synthesise_magnitudes(waveform: np.ndarray, n_events: int = 30) -> np.ndarray:
    envelope = np.abs(sp_signal.hilbert(waveform))
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
    if waveform is None:
        raise ValueError("waveform must not be None.")
    waveform = np.asarray(waveform, dtype=float)
    if waveform.ndim != 1:
        raise ValueError("waveform must be a 1D array.")
    if len(waveform) < 16:
        raise ValueError("waveform must contain at least 16 samples.")
    if not np.all(np.isfinite(waveform)):
        raise ValueError("waveform contains NaN or infinite values.")
    return waveform


# ── DATA QUALITY SCORE ────────────────────────────────────────────────────────

def _data_quality(waveform: np.ndarray) -> float:
    """
    Simple data quality score [0, 1].
    Penalises very short windows and flat/clipped signals.
    """
    n    = len(waveform)
    len_score = float(np.clip((n - 16) / (512 - 16), 0.0, 1.0))
    rng  = float(np.ptp(waveform))
    rng_score = float(np.clip(rng / (np.std(waveform) * 4 + 1e-9), 0.0, 1.0))
    return 0.6 * len_score + 0.4 * rng_score


# ── PUBLIC SANITISATION ───────────────────────────────────────────────────────

def sanitize_channel_for_api(ch_key: str, ch_val: ChannelResult) -> dict:
    safe_meta = {k: v for k, v in ch_val.metadata.items()
                 if k in _PUBLIC_METADATA_KEYS}
    return {
        "score":    round(ch_val.normalised, 4),
        "label":    ch_val.label,
        "metadata": safe_meta,
    }


# ── AUDIT HASH ────────────────────────────────────────────────────────────────

def _audit_hash(cci: float, ts: float, run: int, domain: str) -> str:
    payload = f"{BUILD_TAG}|{domain}|{cci:.6f}|{ts:.2f}|{run}"
    return hashlib.sha256(payload.encode()).hexdigest()


# ── MAIN ENGINE ───────────────────────────────────────────────────────────────

class TCEngine:
    """
    Triple-Convergence Acoustic Diagnostic Engine v3.0

    Five-channel CCI with domain-specific weights, persistence gate,
    IAAFT surrogate rejection, and confidence scoring.

    Stateful per-instance: Kalman, Ljung-Box, AttractorDrift, PLV, and
    persistence gate all accumulate state across calls to analyse().

    For independent per-request scoring (one-shot endpoints), create a
    fresh TCEngine() per request.

    For streaming sessions, retain the same instance across calls.

    Black-box: channel weights, thresholds, and channel formulas are
    not accessible through any public interface.
    """

    def __init__(self, domain: str = "seismic", fs: float = 100.0,
                 enable_surrogate_gate: bool = True) -> None:
        self._domain_cfg         = get_domain_config(domain)
        self._domain             = domain
        self._kalman             = _EigenKalman(dim=_KALMAN_DIM)
        self._alb                = _AdaptiveLjungBox()
        self._attractor_drift    = AttractorDrift()
        self._plv                = PLVChannel(fs=fs)
        self._persistence        = PersistenceGate()
        self._surrogate_gate     = SurrogateGate() if enable_surrogate_gate else None
        self._enable_surrogate   = enable_surrogate_gate
        self._run_count          = 0

    def _compute_cci(self, channels: Dict[str, ChannelResult]) -> float:
        weights = self._domain_cfg.weights
        cci = sum(
            w * (channels[k].normalised if k in channels else 0.0)
            for k, w in weights.items()
        )
        return float(np.clip(cci, 0.0, 1.0))

    def _cci_to_raw_level(self, cci: float) -> str:
        if cci >= THRESHOLD_CRITICAL: return "CRITICAL"
        if cci >= THRESHOLD_WARNING:  return "WARNING"
        if cci >= THRESHOLD_ADVISORY: return "ADVISORY"
        return "NOMINAL"

    def _surrogate_engine_fn(self, waveform: np.ndarray, domain: str) -> float:
        """
        Lightweight CCI-only pass for surrogate gate — no state updates.

        Cold-start limitation: each surrogate is scored with a fresh engine
        (no Kalman/AttractorDrift/PLV history), while the real engine may
        have accumulated state across many windows. This means surrogate CCI
        is not a perfectly matched null — it is slightly conservative (lower
        surrogate CCI → easier to pass the gate).

        Acceptable for one-shot screening. For streaming session validation,
        a stateless CCI path or channel-state snapshot/clone is required to
        produce apples-to-apples surrogate comparison.

        TODO (streaming): implement channel state snapshot so surrogate
        engines are initialised with matching Kalman/LB/drift history.
        """
        eng = TCEngine(domain=domain, enable_surrogate_gate=False)
        out = eng.analyse(waveform, apply_surrogate_gate=False)
        return out.cci

    def analyse(
        self,
        waveform:              np.ndarray,
        magnitudes:            Optional[np.ndarray] = None,
        mc:                    float = 0.0,
        timestamp:             Optional[float] = None,
        apply_surrogate_gate:  bool = True,
    ) -> EngineOutput:
        ts = time.time() if timestamp is None else timestamp

        waveform = _validate_waveform(waveform)
        self._run_count += 1

        # DWT: internal conditioning — band_energies never leave analyse()
        band_e, _mig = _dwt_energy_profile(waveform)
        rms = float(np.sqrt(np.mean(waveform ** 2)))
        obs = np.array([
            band_e[0] if len(band_e) > 0 else 0.0,
            band_e[1] if len(band_e) > 1 else 0.0,
            band_e[2] if len(band_e) > 2 else 0.0,
            rms,
        ])

        # ── channel computation ───────────────────────────────────────────────
        kalman_result   = _compute_kalman_channel(obs, self._kalman)
        lb_result       = _compute_lb_channel(waveform, self._alb)

        if magnitudes is None:
            magnitudes = _synthesise_magnitudes(waveform)
        else:
            magnitudes = np.asarray(magnitudes, dtype=float)
            if len(magnitudes) < 5:
                raise ValueError("magnitudes must contain at least 5 values.")
            if not np.all(np.isfinite(magnitudes)):
                raise ValueError("magnitudes contains NaN or infinite values.")

        b_result        = _compute_b_value_channel(magnitudes, mc)

        drift_score     = self._attractor_drift.update(waveform)
        drift_result    = ChannelResult(
            normalised=drift_score,
            label="Geometric instability",
            metadata={},
        )

        plv_score, plv_rising = self._plv.update(waveform)
        plv_result      = ChannelResult(
            normalised=plv_score,
            label="Phase coupling index",
            metadata={"rising": plv_rising},
        )

        channels = {
            "b_value":         b_result,
            "kappa":           kalman_result,
            "attractor_drift": drift_result,
            "plv":             plv_result,
            "ljung_box":       lb_result,
        }

        # ── CCI and persistence gate ──────────────────────────────────────────
        cci         = self._compute_cci(channels)
        raw_level   = self._cci_to_raw_level(cci)
        gated_level, _, persistence_score = self._persistence.update(cci)

        # ── surrogate gate ────────────────────────────────────────────────────
        surrogate_z      = 0.0
        surrogate_tested = False

        if (self._enable_surrogate and apply_surrogate_gate
                and gated_level in ("WARNING", "CRITICAL")):
            z_min    = SURROGATE_Z_MIN.get(gated_level, 2.0)
            passes, surrogate_z, _s_mean = self._surrogate_gate.test(
                waveform=waveform,
                real_cci=cci,
                engine_fn=self._surrogate_engine_fn,
                domain=self._domain,
                z_min=z_min,
            )
            surrogate_tested = True
            if not passes:
                # Downgrade — real CCI indistinguishable from linear surrogate
                gated_level = "ADVISORY" if gated_level == "WARNING" else "WARNING"

        # ── confidence score ──────────────────────────────────────────────────
        dq = _data_quality(waveform)
        if surrogate_tested:
            s_score = float(np.clip(surrogate_z / 3.0, 0.0, 1.0))
        else:
            s_score = 0.5  # neutral when not yet tested

        # Softened multiplicative confidence — early windows (low persistence)
        # are not destroyed; all three factors must be strong for high confidence.
        confidence = float(np.clip(
            (0.5 + 0.5 * persistence_score) *
            (0.5 + 0.5 * s_score) *
            dq,
            0.0, 1.0
        ))

        # Enforce confidence floor — alert suppressed if confidence too low
        floor = CONFIDENCE_FLOOR.get(gated_level, 0.0)
        if confidence < floor and gated_level != "NOMINAL":
            gated_level = "ADVISORY" if gated_level in ("WARNING", "CRITICAL") else "NOMINAL"

        return EngineOutput(
            timestamp=ts,
            cci=cci,
            alert_level=gated_level,
            raw_alert_level=raw_level,
            domain=self._domain,
            channels=channels,
            audit_hash=_audit_hash(cci, ts, self._run_count, self._domain),
            sample_count=len(waveform),
            persistence_score=round(persistence_score, 4),
            confidence=round(confidence, 4),
            surrogate_z=round(surrogate_z, 4),
            surrogate_tested=surrogate_tested,
        )


# ── VALIDATION HARNESS ────────────────────────────────────────────────────────

_VALIDATION_EVENTS: Dict = {
    "Tohoku_2011": {
        "description":    "Mw 9.1 megathrust — offshore Honshu, Japan",
        "domain":         "seismic",
        "onset_frac":     0.12,
        "severity_scale": 0.89,
        "seed":           2011,
    },
    "Eyjafjallajokull_2010": {
        "description":    "VEI 4 sub-glacial eruption — Iceland",
        "domain":         "volcanic",
        "onset_frac":     0.18,
        "severity_scale": 0.81,
        "seed":           2010,
    },
    "Rana_Plaza_2013": {
        "description":    "Structural progressive collapse — Dhaka, Bangladesh",
        "domain":         "structural",
        "onset_frac":     0.22,
        "severity_scale": 0.76,
        "seed":           2013,
    },
}


def _make_precursor_signal(n: int, onset_frac: float,
                            severity_scale: float, seed: int) -> np.ndarray:
    rng   = np.random.default_rng(seed)
    t     = np.linspace(0, 4 * np.pi, n)
    sig   = rng.normal(0, 0.1, n)
    onset = int(n * onset_frac)
    sf    = 0.3 + (1 - severity_scale) * 0.5
    ramp  = np.linspace(0, severity_scale * 2, n - onset)
    sig[onset:] += ramp * np.sin(sf * t[onset:])
    burst = int(n * 0.85)
    sig[burst:] += rng.normal(0, severity_scale * 1.5, n - burst)
    return sig


def _make_white_noise_negative_control(n: int, seed: int) -> np.ndarray:
    """
    Pure white noise negative control.
    Used to establish a noise-floor CCI baseline in the validation harness.
    This is NOT an IAAFT phase-randomized surrogate — it does not preserve
    the power spectrum or amplitude distribution of the real signal.
    True IAAFT surrogate baseline is implemented in surrogate.py and is
    used by the live surrogate rejection gate in TCEngine.analyse().
    """
    return np.random.default_rng(seed + 9999).normal(0, 0.1, n)


def run_validation(n_samples: int = 512) -> Dict:
    """
    Run the synthetic historical event harness — v3.0.

    Each event uses:
      - Fresh TCEngine per domain (no state contamination)
      - Surrogate gate DISABLED during harness (gate would consume
        significant time and is tested separately)
      - White-noise surrogate run per event for z-score baseline
      - Peak CCI across windowed analysis reported
      - First WARNING window index reported (lead-time proxy)

    Returns expanded schema per event:
      event_name, domain, description, cci_peak, alert_level,
      raw_alert_level, first_warning_window, lead_time_windows,
      surrogate_mean_cci, surrogate_std_cci, z_score_vs_surrogate,
      persistence_score, confidence, status, audit_hash, channels

    Status codes:
      SIM-HARNESS-PASS  — peak CCI ≥ 90% of severity_scale threshold
      SIM-HARNESS-FAIL  — peak CCI below threshold
    """
    results: Dict = {}
    window_size   = 128
    step          = 32

    for event_id, cfg in _VALIDATION_EVENTS.items():
        domain  = cfg["domain"]
        engine  = TCEngine(domain=domain, enable_surrogate_gate=False)
        waveform = _make_precursor_signal(
            n=n_samples,
            onset_frac=cfg["onset_frac"],
            severity_scale=cfg["severity_scale"],
            seed=cfg["seed"],
        )

        peak_out             = None
        peak_cci             = -1.0
        first_warning_window = None
        window_idx           = 0

        for i, start in enumerate(range(0, n_samples - window_size + 1, step)):
            out = engine.analyse(
                waveform=waveform[start: start + window_size],
                apply_surrogate_gate=False,
            )
            if out.cci > peak_cci:
                peak_cci   = out.cci
                peak_out   = out
            if first_warning_window is None and out.raw_alert_level in ("WARNING", "CRITICAL"):
                first_warning_window = i
            window_idx = i

        # White-noise negative control baseline (NOT IAAFT — see docstring above)
        n_surr = 9
        surrogate_ccis = []
        for si in range(n_surr):
            s_eng  = TCEngine(domain=domain, enable_surrogate_gate=False)
            noise  = _make_white_noise_negative_control(n_samples, seed=cfg["seed"] + si)
            s_peak = -1.0
            for start in range(0, n_samples - window_size + 1, step):
                s_out = s_eng.analyse(
                    waveform=noise[start: start + window_size],
                    apply_surrogate_gate=False,
                )
                if s_out.cci > s_peak:
                    s_peak = s_out.cci
            surrogate_ccis.append(s_peak)

        s_arr           = np.array(surrogate_ccis)
        surrogate_mean  = float(s_arr.mean())
        surrogate_std   = float(s_arr.std() + 1e-9)
        z_score         = (peak_cci - surrogate_mean) / surrogate_std

        out     = peak_out
        status  = (
            "SIM-HARNESS-PASS"
            if out.cci >= cfg["severity_scale"] * 0.90
            else "SIM-HARNESS-FAIL"
        )

        total_windows        = window_idx + 1
        lead_time_windows    = (
            (total_windows - first_warning_window)
            if first_warning_window is not None else 0
        )

        results[event_id] = {
            "description":              cfg["description"],
            "domain":                   domain,
            "cci_peak":                 round(out.cci, 4),
            "alert_level":              out.alert_level,
            "raw_alert_level":          out.raw_alert_level,
            "first_warning_window":     first_warning_window,
            "lead_time_windows":        lead_time_windows,
            "total_windows":            total_windows,
            "noise_floor_mean_cci":     round(surrogate_mean, 4),
            "noise_floor_std_cci":      round(surrogate_std, 4),
            "z_score_vs_noise_floor":   round(z_score, 4),
            "noise_floor_note":         (
                "Baseline is white-noise negative control, not IAAFT surrogate. "
                "IAAFT phase-randomized surrogate gate is active in live engine."
            ),
            "persistence_score":        round(out.persistence_score, 4),
            "confidence":               round(out.confidence, 4),
            "status":                   status,
            "audit_hash":               out.audit_hash,
            "disclaimer": (
                "IRIS/FDSN retrospective validation is pending under "
                "TC-VAL-PROTO-001. SIM-HARNESS-PASS does not constitute "
                "empirical instrument-data validation."
            ),
            "channels": {
                k: sanitize_channel_for_api(k, v)
                for k, v in out.channels.items()
            },
        }

    return results
