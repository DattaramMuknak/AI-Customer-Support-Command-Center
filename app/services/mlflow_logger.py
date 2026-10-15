"""
MLflow logging service — records each agent invocation as an MLflow run
for observability and offline evaluation. Logs heuristic quality metrics
and prompt version tags alongside core latency/confidence metrics.
"""

import mlflow

from app.core.config import settings
from app.core.logging import get_logger
from app.services.evaluation import compute_all_heuristics
from app.services.prompt_registry import get_prompt_version

logger = get_logger(__name__)

_mlflow_configured = False


def _ensure_mlflow_configured() -> None:
    global _mlflow_configured
    if not _mlflow_configured:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.mlflow_experiment_name)
        _mlflow_configured = True


def log_agent_run(
    ticket_id: str,
    agent_used: str,
    user_message: str,
    response: str,
    confidence_score: float,
    escalated: bool,
    latency_ms: int,
    sources: list[str],
    retrieved_context: str = "",
) -> None:
    """
    Log a single agent invocation as an MLflow run, including:
    - core metrics (latency, confidence, escalation)
    - heuristic quality metrics (groundedness, length score, unsafe pattern flag)
    - the prompt version used by this agent (for correlating prompt changes -> quality)
    Fails silently if the MLflow server is unreachable — observability must never
    break the user-facing request.
    """
    try:
        _ensure_mlflow_configured()
        heuristics = compute_all_heuristics(response, retrieved_context)
        prompt_version = get_prompt_version(agent_used.replace("_agent", ""))

        with mlflow.start_run(run_name=f"ticket-{ticket_id}"):
            mlflow.log_param("agent_used", agent_used)
            mlflow.log_param("ticket_id", ticket_id)
            mlflow.log_param("num_sources", len(sources))
            mlflow.log_param("prompt_version", prompt_version)

            mlflow.log_metric("confidence_score", confidence_score)
            mlflow.log_metric("latency_ms", latency_ms)
            mlflow.log_metric("escalated", int(escalated))
            mlflow.log_metric("length_score", heuristics["length_score"])
            mlflow.log_metric("groundedness_score", heuristics["groundedness_score"])
            mlflow.log_metric(
                "has_unsafe_pattern", int(heuristics["has_unsafe_pattern"])
            )

            mlflow.log_text(user_message, "user_message.txt")
            mlflow.log_text(response, "agent_response.txt")
            if retrieved_context:
                mlflow.log_text(retrieved_context, "retrieved_context.txt")
    except Exception as e:  # noqa: BLE001
        # Observability should never break the user-facing request
        logger.warning("mlflow_logging_failed", error=str(e))
