"""Quality Scoring Engine — Track and score AI model performance.

Evaluates model responses across multiple dimensions:
- Latency (response time)
- Cost efficiency (tokens per dollar)
- Output quality (heuristic: length, structure, code blocks)
- Task completion (did the response address the prompt?)

Stores results in SQLite at ~/.ucore/indices/quality.db for historical analysis.

Usage:
    scorer = QualityScorer.get()
    score = scorer.score_response(
        task_type="implement",
        model="qwen2.5-coder:3b",
        provider="ollama",
        prompt="Write a function...",
        response="def foo(): ...",
        latency_ms=1200,
        cost_usd=0.0,
    )
    best = scorer.get_best_model("implement")
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.quality_scorer")

DB_PATH = Path.home() / ".ucore" / "indices" / "quality.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS quality_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    task_type TEXT NOT NULL,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    cost_tier TEXT DEFAULT 'unknown',
    latency_ms REAL,
    cost_usd REAL DEFAULT 0.0,
    prompt_tokens INTEGER,
    response_tokens INTEGER,
    output_length INTEGER,
    has_code INTEGER DEFAULT 0,
    has_structure INTEGER DEFAULT 0,
    error INTEGER DEFAULT 0,
    score REAL NOT NULL,
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_qlog_task_type
    ON quality_log(task_type);
CREATE INDEX IF NOT EXISTS idx_qlog_model
    ON quality_log(model);
CREATE INDEX IF NOT EXISTS idx_qlog_timestamp
    ON quality_log(timestamp);
"""


class QualityScorer:
    """Score and track AI model response quality."""

    _instance: "QualityScorer | None" = None

    WEIGHTS = {
        "latency": 0.15,
        "cost": 0.20,
        "output": 0.30,
        "completion": 0.35,
    }

    def __init__(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)

    @classmethod
    def get(cls) -> "QualityScorer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def score_response(
        self,
        task_type: str,
        model: str,
        provider: str,
        prompt: str,
        response: str,
        latency_ms: float,
        cost_usd: float = 0.0,
        cost_tier: str = "unknown",
        prompt_tokens: int | None = None,
        response_tokens: int | None = None,
        had_error: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> float:
        """Score a model response. Returns 0.0-1.0."""
        output_length = len(response) if response else 0
        has_code = 1 if self._detect_code(response) else 0
        has_structure = 1 if self._detect_structure(response) else 0

        latency_score = self._score_latency(latency_ms, task_type)
        cost_score = self._score_cost(cost_usd, output_length)
        output_score = self._score_output(output_length, has_code, has_structure)
        completion_score = self._score_completion(prompt, response, had_error)

        total = (
            self.WEIGHTS["latency"] * latency_score
            + self.WEIGHTS["cost"] * cost_score
            + self.WEIGHTS["output"] * output_score
            + self.WEIGHTS["completion"] * completion_score
        )
        score = round(max(0.0, min(1.0, total)), 4)

        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            """
            INSERT INTO quality_log
            (timestamp, task_type, model, provider, cost_tier,
             latency_ms, cost_usd, prompt_tokens, response_tokens,
             output_length, has_code, has_structure, error,
             score, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now, task_type, model, provider, cost_tier,
                latency_ms, cost_usd,
                prompt_tokens or 0, response_tokens or 0,
                output_length, has_code, has_structure,
                1 if had_error else 0, score,
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        return score

    def get_best_model(
        self, task_type: str, min_samples: int = 3,
    ) -> dict[str, Any] | None:
        """Get the best-performing model for a task type."""
        rows = self._conn.execute(
            """
            SELECT model, provider, cost_tier,
                   AVG(score) as avg_score,
                   AVG(latency_ms) as avg_latency,
                   AVG(cost_usd) as avg_cost,
                   COUNT(*) as samples
            FROM quality_log
            WHERE task_type = ? AND error = 0
            GROUP BY model
            HAVING COUNT(*) >= ?
            ORDER BY avg_score DESC
            LIMIT 1
            """,
            (task_type, min_samples),
        ).fetchall()

        if not rows:
            return None

        row = rows[0]
        return {
            "model": row["model"],
            "provider": row["provider"],
            "cost_tier": row["cost_tier"],
            "avg_score": round(row["avg_score"], 4),
            "avg_latency_ms": round(row["avg_latency"], 1),
            "avg_cost_usd": round(row["avg_cost"], 6),
            "samples": row["samples"],
        }

    def get_model_rankings(
        self, task_type: str | None = None, limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get ranked list of models by quality score."""
        if task_type:
            rows = self._conn.execute(
                """
                SELECT model, provider, cost_tier,
                       AVG(score) as avg_score,
                       AVG(latency_ms) as avg_latency,
                       AVG(cost_usd) as avg_cost,
                       COUNT(*) as samples
                FROM quality_log
                WHERE task_type = ? AND error = 0
                GROUP BY model
                ORDER BY avg_score DESC
                LIMIT ?
                """,
                (task_type, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT model, provider, cost_tier,
                       AVG(score) as avg_score,
                       AVG(latency_ms) as avg_latency,
                       AVG(cost_usd) as avg_cost,
                       COUNT(*) as samples
                FROM quality_log
                WHERE error = 0
                GROUP BY model
                ORDER BY avg_score DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "model": r["model"],
                "provider": r["provider"],
                "cost_tier": r["cost_tier"],
                "avg_score": round(r["avg_score"], 4),
                "avg_latency_ms": round(r["avg_latency"], 1),
                "avg_cost_usd": round(r["avg_cost"], 6),
                "samples": r["samples"],
            }
            for r in rows
        ]

    def get_stats(self) -> dict[str, Any]:
        """Get overall quality statistics."""
        total = self._conn.execute(
            "SELECT COUNT(*) FROM quality_log",
        ).fetchone()[0]

        errors = self._conn.execute(
            "SELECT COUNT(*) FROM quality_log WHERE error = 1",
        ).fetchone()[0]

        avg_score = self._conn.execute(
            "SELECT AVG(score) FROM quality_log",
        ).fetchone()[0]

        by_task = {}
        for row in self._conn.execute(
            "SELECT task_type, COUNT(*) as cnt, AVG(score) as avg "
            "FROM quality_log GROUP BY task_type",
        ).fetchall():
            by_task[row["task_type"]] = {
                "count": row["cnt"],
                "avg_score": round(row["avg"], 4),
            }

        return {
            "total_records": total,
            "errors": errors,
            "avg_score": round(avg_score or 0, 4),
            "by_task_type": by_task,
        }

    def _score_latency(self, latency_ms: float, task_type: str) -> float:
        thresholds = {
            "fast": 500, "coder": 3000, "reviewer": 5000,
            "architect": 8000, "debugger": 3000, "docgen": 4000,
            "any": 4000,
        }
        target = thresholds.get(task_type, 4000)
        if latency_ms <= target:
            return 1.0
        if latency_ms <= target * 3:
            return 0.7
        if latency_ms <= target * 5:
            return 0.4
        return 0.1

    def _score_cost(self, cost_usd: float, output_length: int) -> float:
        if cost_usd == 0.0:
            return 1.0
        if output_length == 0:
            return 0.0
        cost_per_char = cost_usd / output_length
        if cost_per_char < 0.00001:
            return 1.0
        if cost_per_char < 0.0001:
            return 0.8
        if cost_per_char < 0.001:
            return 0.5
        return 0.2

    def _score_output(
        self, length: int, has_code: int, has_structure: int,
    ) -> float:
        score = 0.0
        if 100 <= length <= 10000:
            score += 0.4
        elif length > 50:
            score += 0.2
        if has_code:
            score += 0.3
        if has_structure:
            score += 0.3
        return min(1.0, score)

    def _score_completion(
        self, prompt: str, response: str, had_error: bool,
    ) -> float:
        if had_error:
            return 0.0
        if not response or len(response) < 10:
            return 0.1
        prompt_lower = prompt.lower()
        response_lower = response.lower()
        if "?" in prompt:
            indicators = [
                "yes", "no", "here", "the answer", "solution",
                "you can", "should", "recommend", "suggest",
            ]
            if any(w in response_lower for w in indicators):
                return 0.8
        if any(w in prompt_lower for w in ["code", "function", "implement", "write"]):
            if self._detect_code(response):
                return 0.9
        if len(response) > 100:
            return 0.7
        return 0.4

    def _detect_code(self, text: str) -> bool:
        if "```" in text:
            return True
        indicators = [
            "def ", "class ", "import ", "function ",
            "const ", "let ", "var ", "return ",
            "if (", "for (", "while (", "async ",
        ]
        return any(ind in text for ind in indicators)

    def _detect_structure(self, text: str) -> bool:
        markers = ["## ", "### ", "- ", "1. ", "**", "```", "| ", "---"]
        return any(m in text for m in markers)
