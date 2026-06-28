"""
spectral_geometry.py
====================
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
Document: TC-ENG-GEO-001

AttractorDrift Channel
----------------------
Tracks the recurrence-threshold epsilon required to maintain a constant
Recurrence Rate (RR) in reconstructed phase space.

In stressed media (faults, crack networks, fatigue damage), the system's
state-space geometry changes measurably before any macro-event occurs.
When the threshold required to maintain a 3% recurrence rate begins to
oscillate, the system is losing stable attractor geometry — a
pre-bifurcation signal that typically precedes observable threshold
crossings in amplitude-domain channels.

This is a dynamical-systems channel. It does not assume the signal is a
linear stochastic process. It detects geometric instability, not volume
of noise.

Trade secret: epsilon computation parameters, scoring weights, and
history weighting are not exposed in any API response.
"""
from __future__ import annotations

import hashlib
import numpy as np
from collections import deque
from typing import Deque


class AttractorDrift:
    """
    Recurrence-threshold drift tracker.

    Parameters
    ----------
    target_rr : float
        Target recurrence rate — fraction of point-pairs considered
        "recurrent." Lower = more sensitive, slower to saturate.
    max_points : int
        Maximum embedded points used in distance computation.
        Hard cap prevents O(N²) blowup on long waveforms.
    history_len : int
        Number of consecutive windows retained for drift scoring.
    tau : int
        Delay embedding lag (samples).
    embed_dim : int
        Embedding dimension (Takens: 2*d+1 where d = attractor dimension).
    """

    def __init__(
        self,
        target_rr: float = 0.03,
        max_points: int = 512,
        history_len: int = 20,
        tau: int = 2,
        embed_dim: int = 3,
    ) -> None:
        if embed_dim < 2:
            raise ValueError("embed_dim must be >= 2.")
        if tau < 1:
            raise ValueError("tau must be >= 1.")
        if not 0.001 <= target_rr <= 0.25:
            raise ValueError("target_rr must be between 0.001 and 0.25.")
        if max_points < 16:
            raise ValueError("max_points must be at least 16.")
        if history_len < 5:
            raise ValueError("history_len must be at least 5.")
        self.target_rr  = target_rr
        self.max_points = max_points
        self.tau        = tau
        self.embed_dim  = embed_dim
        self._history: Deque[float] = deque(maxlen=history_len)
        self.last_epsilon = 0.0   # internal debug — never forwarded to API
        self.last_cv      = 0.0   # internal debug — never forwarded to API
        self.last_slope   = 0.0   # internal debug — never forwarded to API

    # ── internal ──────────────────────────────────────────────────────────────

    def _embed(self, x: np.ndarray) -> np.ndarray:
        """Delay-coordinate embedding of 1-D signal x.

        Performance note: currently uses a Python list comprehension.
        Can be replaced with np.lib.stride_tricks.sliding_window_view
        for a vectorized implementation when waveform lengths grow beyond
        the current max_points cap.
        """
        n = len(x) - (self.embed_dim - 1) * self.tau
        if n <= 8:
            return np.empty((0, self.embed_dim))
        return np.array([
            x[i: i + self.embed_dim * self.tau: self.tau]
            for i in range(n)
        ])

    def _epsilon(self, x: np.ndarray) -> float:
        """
        Compute adaptive recurrence threshold epsilon for waveform x.
        Returns the pairwise distance at which target_rr fraction of
        point-pairs are considered recurrent.

        Raw epsilon value is internal — never forwarded to API response.
        """
        x = np.asarray(x, dtype=float)
        if x.ndim != 1:
            raise ValueError("waveform must be a 1D array.")
        if not np.all(np.isfinite(x)):
            raise ValueError("waveform contains NaN or infinite values.")
        if np.std(x) < 1e-12:
            return 0.0
        if len(x) < 64:
            return 0.0

        # Normalise to zero-mean unit-variance before embedding.
        # Decouples recurrence geometry from signal amplitude — epsilon
        # tracks shape change, not volume change.
        x = (x - np.mean(x)) / (np.std(x) + 1e-12)

        embedded = self._embed(x)
        if len(embedded) < 16:
            return 0.0

        # Downsample to max_points to cap memory/time
        if len(embedded) > self.max_points:
            idx      = np.linspace(0, len(embedded) - 1,
                                   self.max_points, dtype=int)
            embedded = embedded[idx]

        # Sample random non-self pairwise distances.
        # This keeps memory flat while preserving quantile accuracy.
        n          = len(embedded)
        max_pairs  = min(n * (n - 1) // 2, 20_000)
        seed_bytes = np.round(embedded[:64, 0], 6).tobytes()
        seed       = int.from_bytes(hashlib.blake2b(seed_bytes, digest_size=4).digest(), "little")
        rng        = np.random.default_rng(seed)
        i_idx      = rng.integers(0, n, size=max_pairs)
        j_idx      = rng.integers(0, n, size=max_pairs)
        mask       = i_idx != j_idx
        i_idx, j_idx = i_idx[mask], j_idx[mask]

        if len(i_idx) < 100:
            return 0.0

        diff  = embedded[i_idx] - embedded[j_idx]
        upper = np.sqrt(np.einsum("ij,ij->i", diff, diff))

        if len(upper) == 0:
            return 0.0

        q = float(np.clip(self.target_rr, 0.001, 0.25))
        return float(np.quantile(upper, q))

    # ── public ────────────────────────────────────────────────────────────────

    def update(self, waveform: np.ndarray) -> float:
        """
        Update drift history with epsilon from current waveform window.

        Returns
        -------
        float in [0, 1]
            0 = stable attractor geometry (or insufficient data)
            1 = highly unstable / pre-bifurcation geometry
        Returns 0.0 until at least 5 windows are accumulated — confidence
        module in tc_engine_v3 penalizes low data quality separately.
        """
        eps = self._epsilon(waveform)

        if eps <= 0.0:
            self.last_epsilon = 0.0
            self.last_cv      = 0.0
            self.last_slope   = 0.0
            return 0.0

        self._history.append(eps)

        if len(self._history) < 5:
            self.last_epsilon = eps
            self.last_cv      = 0.0
            self.last_slope   = 0.0
            return 0.0

        arr  = np.array(self._history, dtype=float)
        mean = np.mean(arr) + 1e-9
        cv   = np.std(arr) / mean          # oscillation / spread

        # Directional drift: normalised slope of epsilon trend.
        # CV alone misses steady monotonic drift (low std, rising mean).
        # Slope catches pre-bifurcation ramp that CV would score near zero.
        t     = np.arange(len(arr), dtype=float)
        slope = np.polyfit(t, arr, 1)[0] / mean

        # Internal calibration scaling.
        score             = float(np.clip((cv * 4.0) + (abs(slope) * 8.0), 0.0, 1.0))
        self.last_epsilon = eps    # internal debug — never forwarded to API
        self.last_cv      = cv     # internal debug — never forwarded to API
        self.last_slope   = slope  # internal debug — never forwarded to API
        return score

    def quality(self) -> float:
        """
        History fill fraction [0, 1].
        Allows the main engine to reduce confidence when AttractorDrift
        has accumulated fewer than history_len windows.
        0.0 = no history; 1.0 = fully warmed up.
        """
        return min(len(self._history) / self._history.maxlen, 1.0)

    def reset(self) -> None:
        """Clear history — call between independent analysis sessions."""
        self._history.clear()
        self.last_epsilon = 0.0
        self.last_cv      = 0.0
        self.last_slope   = 0.0
