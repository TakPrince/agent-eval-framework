"""
utils/experiment_tracker.py
-----------------------------
Phase 7: Lightweight experiment tracking and reproducibility layer.

Design rules
~~~~~~~~~~~~
* Pure stdlib only — uuid, json, datetime, pathlib, os
* No external tools (no wandb, mlflow, sqlite)
* Never crashes the eval pipeline — all methods wrapped in try/except
* Three output files per run stored under evals/experiments/:
    exp_<id>_config.json   → run configuration snapshot
    exp_<id>_results.json  → full enriched results
    exp_<id>_traces.json   → steps-only audit trail (lightweight)
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.logger import get_logger

logger = get_logger()

# All experiment files land here
EXPERIMENTS_DIR = Path("evals/experiments")


class ExperimentTracker:
    """
    Tracks a single evaluation run end-to-end.

    Usage
    -----
        tracker = ExperimentTracker(models, config)
        # ... run evaluation ...
        tracker.save_config(config)
        tracker.save_results(all_results)
        tracker.save_traces(all_results)
    """

    def __init__(self, models: list, config: Any):
        # ── unique run identity ───────────────────────────────────
        self.experiment_id: str = str(uuid.uuid4())

        # ── metadata snapshot taken at construction time ──────────
        self.metadata: dict = {
            "experiment_id": self.experiment_id,
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "models":        [m.get("name", str(m)) for m in models],
            "dataset":       getattr(config, "dataset_name", "unknown"),
        }

        # ── ensure output directory exists ───────────────────────
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"[Tracker] Experiment started → id={self.experiment_id}")

    # ─────────────────────────────────────────────────────────────
    # File path helpers
    # ─────────────────────────────────────────────────────────────

    def _path(self, suffix: str) -> Path:
        """Build a namespaced path: evals/experiments/exp_<id>_<suffix>.json"""
        return EXPERIMENTS_DIR / f"exp_{self.experiment_id}_{suffix}.json"

    # ─────────────────────────────────────────────────────────────
    # Public: save_config
    # ─────────────────────────────────────────────────────────────

    def save_config(self, config: Any) -> None:
        """
        Snapshot the run configuration so the experiment is reproducible.

        Handles config objects, dicts, and anything str()-able.
        """
        try:
            if hasattr(config, "__dict__"):
                config_data = vars(config)
            elif isinstance(config, dict):
                config_data = config
            else:
                config_data = {"raw": str(config)}

            payload = {
                **self.metadata,
                "config": config_data,
            }
            self._write(self._path("config"), payload)
            logger.info(f"[Tracker] Config saved → {self._path('config')}")

        except Exception as e:
            logger.error(f"[Tracker] save_config failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # Public: save_results
    # ─────────────────────────────────────────────────────────────

    def save_results(self, results: list) -> None:
        """
        Save full enriched results (all fields) for post-hoc analysis.
        """
        try:
            payload = {
                **self.metadata,
                "total_queries": len(results),
                "results":       results,
            }
            self._write(self._path("results"), payload)
            logger.info(f"[Tracker] Results saved → {self._path('results')}")

        except Exception as e:
            logger.error(f"[Tracker] save_results failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # Public: save_traces
    # ─────────────────────────────────────────────────────────────

    def save_traces(self, results: list) -> None:
        """
        Extract and store only the steps audit trail per query.

        Traces are stored separately so they can be inspected without
        loading the full results payload — useful for debugging retries
        and trajectory analysis without noise from SQL/score fields.
        """
        try:
            traces = []
            for r in results:
                traces.append({
                    "model":             r.get("model"),
                    "query":             r.get("query"),
                    "predicted_sql":     r.get("predicted_sql"),
                    "final_score":       r.get("final", {}).get("final_score"),
                    "ves_score":         r.get("final", {}).get("ves_score"),
                    "adjusted_score":    r.get("final", {}).get("adjusted_score"),
                    "trajectory_eval":   r.get("final", {}).get("trajectory_eval", {}),
                    "steps":             r.get("steps", []),
                })

            payload = {
                **self.metadata,
                "total_queries": len(traces),
                "traces":        traces,
            }
            self._write(self._path("traces"), payload)
            logger.info(f"[Tracker] Traces saved → {self._path('traces')}")

        except Exception as e:
            logger.error(f"[Tracker] save_traces failed: {e}")

    # ─────────────────────────────────────────────────────────────
    # Internal: atomic JSON write
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _write(path: Path, data: Any) -> None:
        """Write data to path as indented JSON. Uses default=str for safety."""
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4, default=str)