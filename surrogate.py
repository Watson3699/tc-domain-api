"""
surrogate.py
============
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
Document: TC-ENG-SRG-001

Surrogate Rejection Gate
-------------------------
Before confirming any WARNING or CRITICAL alert, the engine compares
the real-signal CCI against CCI computed on amplitude-adjusted Fourier
surrogates (IAAFT — Iteratively Amplitude-Adjusted Fourier Transform).

Surrogates preserve the signal's:
  - Power spectrum (frequency content)
  - Amplitude distribution

But destroy:
  - Nonlinear phase relationships
  - Temporal ordering of structures

If the real CCI is not statistically above surrogate CCI, the
alert is a false alarm driven by linear spectral features, not
genuine nonlinear precursor structure. The alert is downgraded.

This kills the dominant false-alarm pathway in spectral engines.

Algorithm: IAAFT (Schreiber & Schmitz 1996)
  1. Start: random shuffle of x
  2. FFT → impose power spectrum of original
  3. IFFT → rank-order rescale amplitudes to match original distribution
  4. Repeat until convergence or max_iter

Trade secret: n_surrogates, convergence criterion, z_min thresholds
are proprietary and not exposed in API responses.
"""
from __future__ import annotations

import hashlib
import numpy as np
from typing import Tuple


# ── IAAFT surrogate generator ─────────────────────────────────────────────────

def _iaaft_surrogate(x: np.ndarray, max_iter: int = 20,
                     rng: np.random.Generator | None = None) -> np.ndarray:
    """
    Generate one IAAFT surrogate of x.

    Preserves amplitude distribution and power spectrum of x but
    destroys nonlinear phase relationships.
    """
    x = np.asarray(x, dtype=float)

    if len(x) < 16:
        return x.copy()
    if not np.all(np.isfinite(x)):
        raise ValueError("waveform contains NaN or infinite values.")
    if np.std(x) < 1e-12:
        return x.copy()   # flat signal — surrogate is identical

    if rng is None:
        rng = np.random.default_rng()
    n      = len(x)
    sorted_x = np.sort(x)
    target_spectrum = np.abs(np.fft.rfft(x))

    # Initialise with random shuffle
    s = rng.permutation(x)

    for _ in range(max_iter):
        # Impose target power spectrum
        S          = np.fft.rfft(s)
        phases     = np.angle(S)
        S_new      = target_spectrum * np.exp(1j * phases)
        s_ifft     = np.fft.irfft(S_new, n=n)

        # Rank-order rescale to match amplitude distribution
        ranks      = np.argsort(np.argsort(s_ifft))
        s_new      = sorted_x[ranks]

        if np.max(np.abs(s_new - s)) < 1e-8:
            break
        s = s_new

    return s


# ── Surrogate rejection gate ──────────────────────────────────────────────────

class SurrogateGate:
    """
    Compute surrogate CCI distribution and test whether real CCI
    is statistically above the surrogate baseline.

    Parameters
    ----------
    n_surrogates : int
        Number of surrogates to generate per test.
        Default 12 — fast enough for Render one-shot endpoints.
        Use 100 for offline validation runs where latency is not a concern.
        Higher = more accurate null distribution but more compute.
    """

    def __init__(self, n_surrogates: int = 12,
                 seed: int | None = None) -> None:
        if n_surrogates < 2:
            raise ValueError("n_surrogates must be at least 2.")
        self.n_surrogates = n_surrogates
        self.seed         = seed   # None = per-waveform deterministic seeding

    def test(
        self,
        waveform: np.ndarray,
        real_cci: float,
        engine_fn,          # callable: (waveform, domain) -> float (CCI only)
        domain: str,
        z_min: float = 2.0,
    ) -> Tuple[bool, float, float]:
        """
        Test whether real_cci is statistically above surrogate baseline.

        Parameters
        ----------
        waveform : np.ndarray
            Original input waveform.
        real_cci : float
            CCI from the real waveform.
        engine_fn : callable
            Function that accepts (waveform, domain) and returns a float CCI.
            Must be fast (surrogate gate calls it n_surrogates times).
        domain : str
            Domain name passed to engine_fn.
        z_min : float
            Minimum z-score required to confirm the alert.

        Returns
        -------
        passes : bool
            True if real CCI passes the surrogate gate.
        z_score : float
            (real_cci - surrogate_mean) / surrogate_std
        surrogate_mean : float
            Mean CCI across surrogates (for logging — never in API response).
        """
        waveform = np.asarray(waveform, dtype=float)
        if not np.all(np.isfinite(waveform)):
            raise ValueError("waveform contains NaN or infinite values.")
        real_cci = float(np.clip(real_cci, 0.0, 1.0))

        # Deterministic seeding stable across Python restarts.
        # Built-in hash() is salted per-process — blake2b is not.
        # Fixed seed overrides; None falls back to waveform content hash.
        if self.seed is not None:
            rng = np.random.default_rng(self.seed)
        else:
            digest     = hashlib.blake2b(waveform.tobytes(), digest_size=8).digest()
            _hash_seed = int.from_bytes(digest, "little") % (2 ** 32)
            rng        = np.random.default_rng(_hash_seed)
        surrogate_ccis = []

        if z_min <= 0:
            raise ValueError("z_min must be positive.")

        for _ in range(self.n_surrogates):
            s   = _iaaft_surrogate(waveform, rng=rng)
            cci = float(np.clip(engine_fn(s, domain), 0.0, 1.0))
            surrogate_ccis.append(cci)

        arr             = np.array(surrogate_ccis, dtype=float)
        surrogate_mean  = float(arr.mean())
        surrogate_std   = float(arr.std() + 1e-9)
        z_score         = (real_cci - surrogate_mean) / surrogate_std

        passes = z_score >= z_min
        return passes, float(z_score), surrogate_mean
