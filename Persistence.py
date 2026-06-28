"""
persistence.py
==============
AW IP Holdings Inc. | CONFIDENTIAL — Trade Secret
Document: TC-ENG-PER-001

Multi-Window Persistence Gate
------------------------------
A single CCI spike does not make an alert. Background noise can
drive transient threshold crossings in any sensitive detector.

The persistence gate requires an alert level to be confirmed across
multiple consecutive analysis windows before it is declared. This
eliminates single-spike false alarms without meaningfully increasing
detection latency.

Gate rules (from domain_weights.py):
  ADVISORY  : 2 of last 5 windows
  WARNING   : 3 of last 5 windows
  CRITICAL  : 5 of last 8 windows

These rules apply independently per domain session.

Trade secret: gate parameters and persistence scoring are proprietary.
"""
from __future__ import annotations

import numpy as np
from collections import deque
from typing import Deque, Tuple

from domain_weights import PERSISTENCE_GATE, THRESHOLD_ADVISORY, THRESHOLD_WARNING, THRESHOLD_CRITICAL


class PersistenceGate:
    """
    Rolling window persistence gate for alert confirmation.

    Tracks the last N CCI values and returns the highest alert level
    that satisfies the persistence rule. If no level passes, returns
    NOMINAL.
    """

    def __init__(self, max_window: int = 10) -> None:
        # max_window must be >= max gate window across all levels
        self._history: Deque[float] = deque(maxlen=max(
            max_window,
            max(cfg["window"] for cfg in PERSISTENCE_GATE.values())
        ))

    def _raw_level(self, cci: float) -> str:
        """Alert level from raw CCI threshold — without persistence."""
        if cci >= THRESHOLD_CRITICAL: return "CRITICAL"
        if cci >= THRESHOLD_WARNING:  return "WARNING"
        if cci >= THRESHOLD_ADVISORY: return "ADVISORY"
        return "NOMINAL"

    def update(self, cci: float) -> Tuple[str, str, float]:
        """
        Add CCI value and evaluate persistence-gated alert level.

        Returns
        -------
        gated_level : str
            Highest level satisfying the persistence rule.
        raw_level : str
            Level from raw CCI threshold without persistence.
        persistence_score : float
            Fraction of required confirmations achieved for the current raw level.
            1.0 = gate fully satisfied; <1.0 = building toward confirmation.
        """
        cci = float(np.clip(cci, 0.0, 1.0))
        self._history.append(cci)
        arr = np.array(self._history, dtype=float)

        raw_level   = self._raw_level(cci)
        gated_level = "NOMINAL"

        threshold_map = {
            "ADVISORY": THRESHOLD_ADVISORY,
            "WARNING":  THRESHOLD_WARNING,
            "CRITICAL": THRESHOLD_CRITICAL,
        }

        for level in ("CRITICAL", "WARNING", "ADVISORY"):
            cfg        = PERSISTENCE_GATE[level]
            window     = cfg["window"]
            required   = cfg["required"]
            thr        = threshold_map[level]
            recent     = arr[-window:]
            count_high = int(np.sum(recent >= thr))
            if count_high >= required:
                gated_level = level
                break

        if raw_level == "NOMINAL":
            persistence_score = 0.0
        else:
            cfg        = PERSISTENCE_GATE[raw_level]
            recent     = arr[-cfg["window"]:]
            count_high = int(np.sum(recent >= threshold_map[raw_level]))
            persistence_score = float(min(count_high / cfg["required"], 1.0))

        return gated_level, raw_level, persistence_score

    def reset(self) -> None:
        """Clear history between independent sessions."""
        self._history.clear()
