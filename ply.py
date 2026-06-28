"""
plv_channel.py
==============
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
Document: TC-ENG-PLV-001

Phase Locking Value (PLV) Channel
----------------------------------
Amplitude can lie. Phase coupling tells the truth.

PLV measures the consistency of phase angle differences between two
oscillatory modes extracted from the signal. Pre-failure systems
frequently exhibit a characteristic pattern:

  stable (low PLV) → synchronisation surge (PLV spike) → collapse

This pattern is detectable in seismic tremor, volcanic harmonic
tremor, and structural acoustic emission before macroscopic failure
— often 5–15 analysis windows ahead of amplitude-threshold crossings.

Implementation
--------------
Two modes are extracted via band-pass filtering (low-band vs mid-band).
Instantaneous phase is recovered via the analytic signal (Hilbert
transform). PLV is the magnitude of the mean unit-phasor across the
window. A drift history tracks whether PLV is increasing, which is the
pre-failure signature.

Trade secret: band definitions, history weighting, and score mapping
are not exposed in any API response.
"""
from __future__ import annotations

import numpy as np
from collections import deque
from typing import Deque, Tuple

from scipy.signal import butter, sosfiltfilt, hilbert


# ── Band definitions (trade secret — not returned in API responses) ───────────

_BAND_LO_HZ  = (0.5, 4.0)    # Low-frequency tremor / tectonic micro-creep band
_BAND_MID_HZ = (4.0, 20.0)   # Mid-frequency onset / AE precursor band
_DEFAULT_FS  = 100.0          # Assumed sample rate when not provided


# ── helpers ───────────────────────────────────────────────────────────────────

def _bandpass(x: np.ndarray, low: float, high: float,
              fs: float, order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth bandpass via second-order sections.
    Returns zeros (not x) when filtering cannot run — prevents identical
    low/mid bands from producing spurious high PLV."""
    if fs <= 0 or len(x) < order * 6:
        return np.zeros_like(x)
    nyq  = fs / 2.0
    lo   = np.clip(low  / nyq, 1e-4, 0.999)
    hi   = np.clip(high / nyq, 1e-4, 0.999)
    if lo >= hi:
        return np.zeros_like(x)
    sos = butter(order, [lo, hi], btype="band", output="sos")
    return sosfiltfilt(sos, x)


def _instantaneous_phase(x: np.ndarray) -> np.ndarray:
    """Instantaneous phase via Hilbert analytic signal."""
    return np.angle(hilbert(x))


def _plv(phase_a: np.ndarray, phase_b: np.ndarray) -> float:
    """
    Phase Locking Value: magnitude of the mean unit phasor of (φ_a − φ_b).
    Returns value in [0, 1]. 0 = no phase coupling; 1 = perfect phase lock.
    """
    delta = phase_a - phase_b
    return float(np.abs(np.mean(np.exp(1j * delta))))


# ── PLV channel class ─────────────────────────────────────────────────────────

class PLVChannel:
    """
    Phase Locking Value channel with rising-PLV alarm.

    PLV alone is not the signal — the *direction of change* is.
    A stable system has low, consistent PLV. A pre-failure system
    shows PLV rising toward synchronisation.

    Parameters
    ----------
    fs : float
        Sample rate of input waveform (Hz).
    history_len : int
        Number of windows retained for trend scoring.
    """

    def __init__(
        self,
        fs: float = _DEFAULT_FS,
        history_len: int = 20,
    ) -> None:
        if fs <= 0:
            raise ValueError("fs must be positive.")
        if history_len < 5:
            raise ValueError("history_len must be at least 5.")
        self.fs = fs
        self._history: Deque[float] = deque(maxlen=history_len)
        self.last_plv   = 0.0   # internal debug — never forwarded to API
        self.last_slope = 0.0   # internal debug — never forwarded to API

    # ── internal ──────────────────────────────────────────────────────────────

    def _compute_plv(self, waveform: np.ndarray) -> float:
        """
        Extract PLV between low-band and mid-band instantaneous phases.
        Raw PLV value is internal — not forwarded to API response.
        """
        if len(waveform) < 32:
            return 0.0

        lo_sig  = _bandpass(waveform, *_BAND_LO_HZ,  self.fs)
        mid_sig = _bandpass(waveform, *_BAND_MID_HZ, self.fs)

        phi_lo  = _instantaneous_phase(lo_sig)
        phi_mid = _instantaneous_phase(mid_sig)

        return _plv(phi_lo, phi_mid)

    # ── public ────────────────────────────────────────────────────────────────

    def update(self, waveform: np.ndarray) -> Tuple[float, bool]:
        """
        Update PLV history and compute rising-PLV alarm score.

        Returns
        -------
        score : float in [0, 1]
            Normalised rising-PLV alarm. Higher = stronger pre-coupling signal.
        rising : bool
            True if PLV trend is upward over the last 5 windows.
        """
        waveform = np.asarray(waveform, dtype=float)
        if waveform.ndim != 1:
            raise ValueError("waveform must be a 1D array.")
        if not np.all(np.isfinite(waveform)):
            raise ValueError("waveform contains NaN or infinite values.")
        if np.std(waveform) < 1e-12:
            self.last_plv   = 0.0
            self.last_slope = 0.0
            return 0.0, False
        plv_val = self._compute_plv(waveform)
        self._history.append(plv_val)

        if len(self._history) < 5:
            return float(plv_val), False

        arr    = np.array(self._history, dtype=float)
        recent = arr[-5:]

        # Linear trend slope over recent windows
        x      = np.arange(len(recent), dtype=float)
        slope  = float(np.polyfit(x, recent, 1)[0])
        rising = slope > 0.005          # Internal calibration threshold.

        # Score: current PLV amplified by rising-trend bonus
        trend_bonus = float(np.clip(slope * 10.0, 0.0, 0.3))
        score       = float(np.clip(plv_val + trend_bonus, 0.0, 1.0))

        self.last_plv   = plv_val   # internal debug
        self.last_slope = slope     # internal debug

        return score, rising

    def reset(self) -> None:
        """Clear history between independent sessions."""
        self._history.clear()
        self.last_plv   = 0.0
        self.last_slope = 0.0
