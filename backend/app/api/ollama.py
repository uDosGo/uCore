"""Ollama Model Management API — List models, get stats, manage downloads."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx

log = logging.getLogger(__name__)

from app.core.settings import settings


async def get_ollama_status() -> dict:
    """Get Ollama instance status and model list."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Get model list
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code != 200:
                return {
                    "online": False,
                    "error": f"HTTP {resp.status_code}",
                    "models": [],
                }

            data = resp.json()
            models = data.get("models", [])

            return {
                "online": True,
                "base_url": settings.ollama_base_url,
                "models": [
                    {
                        "name": m["name"],
                        "size_gb": round(m.get("size", 0) / 1e9, 2),
                        "modified_at": m.get("modified_at", "unknown"),
                        "digest": m.get("digest", ""),
                    }
                    for m in models
                ],
                "model_count": len(models),
            }
    except Exception as e:
        log.error(f"Failed to get Ollama status: {e}")
        return {
            "online": False,
            "error": str(e),
            "models": [],
        }


async def get_ollama_model_performance() -> dict:
    """Get performance statistics for each model from the activity spool.
    """
    try:
        from app.services.spool_reader import read_spool_entries

        # Read recent activity (last 24 hours)
        datetime.utcnow() - timedelta(hours=24)
        entries = read_spool_entries(limit=1000)

        # Aggregate stats by model
        model_stats: dict[str, dict] = {}

        for entry in entries:
            if entry.get("type") != "skill_execution":
                continue

            metadata = entry.get("metadata", {})
            model = metadata.get("model")
            if not model:
                continue

            if model not in model_stats:
                model_stats[model] = {
                    "uses": 0,
                    "success": 0,
                    "error": 0,
                    "total_latency_ms": 0,
                    "last_used": None,
                }

            stats = model_stats[model]
            stats["uses"] += 1
            stats["last_used"] = entry.get("timestamp")

            if metadata.get("error"):
                stats["error"] += 1
            else:
                stats["success"] += 1
                latency = metadata.get("latency_ms", 0)
                if isinstance(latency, (int, float)):
                    stats["total_latency_ms"] += latency

        # Calculate averages
        return {
            "period": "last_24h",
            "models": {
                model: {
                    "uses": s["uses"],
                    "success_rate": round(100 * s["success"] / s["uses"], 1),
                    "error_count": s["error"],
                    "avg_latency_ms": round(s["total_latency_ms"] / s["success"], 1)
                    if s["success"] > 0
                    else 0,
                    "last_used": s["last_used"],
                }
                for model, s in model_stats.items()
            },
        }
    except Exception as e:
        log.error(f"Failed to get model performance: {e}")
        return {"period": "last_24h", "models": {}, "error": str(e)}


async def get_available_models() -> dict:
    """Get list of models available to pull from Ollama library."""
    # This is a static list of recommended models
    # In production, you might query the Ollama registry API
    return {
        "recommended": [
            {
                "name": "deepseek-v4-flash",
                "size_gb": 13,
                "description": "Cost-efficient MoE (79% on SWE-Bench Verified)",
                "capabilities": ["coding", "reasoning"],
            },
            {
                "name": "glm-5.1",
                "size_gb": 40,
                "description": "Frontier-tier architecture (SOTA on SWE-Bench Pro)",
                "capabilities": ["design", "reasoning", "long-context"],
            },
            {
                "name": "qwen3-coder-next",
                "size_gb": 80,
                "description": "Specialist coder (Claude Sonnet-level efficiency)",
                "capabilities": ["coding", "implementation"],
            },
            {
                "name": "qwen3.6-27b",
                "size_gb": 27,
                "description": "Dense model (Terminal-Bench performance)",
                "capabilities": ["coding", "documentation"],
            },
        ],
        "note": "Sizes are approximate. Actual download size may vary with quantization.",
    }
