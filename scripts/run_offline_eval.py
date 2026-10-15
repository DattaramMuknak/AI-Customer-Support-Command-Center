"""
Offline Evaluation Script — runs the full multi-agent pipeline against a
golden dataset of representative support queries, scores the results
(routing accuracy, keyword coverage, latency, confidence), and logs an
aggregate MLflow run.

Run this:
- Before deploying a new prompt version (regression check)
- On a schedule (e.g. nightly CI job) to catch silent quality drift
- After changing the LLM model or retrieval config

Usage:
    python scripts/run_offline_eval.py
"""

import json
import sys
import time
from pathlib import Path

import mlflow

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.orchestrator import run_agent_pipeline
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.services.prompt_registry import get_all_prompt_versions

configure_logging()
logger = get_logger(__name__)

DATASET_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "golden_eval_dataset.json"
)


def load_golden_dataset() -> list[dict]:
    with open(DATASET_PATH) as f:
        return json.load(f)


def evaluate_single_case(case: dict) -> dict:
    """Run one golden example through the pipeline and score the outcome."""
    start = time.time()
    result = run_agent_pipeline(
        ticket_id=f"eval-{case['id']}", user_message=case["question"]
    )
    elapsed_ms = int((time.time() - start) * 1000)

    actual_route = result.get("route") or _infer_route_from_agent(
        result.get("agent_used", "")
    )
    route_correct = actual_route == case["expected_route"]

    response_lower = result.get("final_response", "").lower()
    keywords_hit = sum(
        1 for kw in case["expected_keywords"] if kw.lower() in response_lower
    )
    keyword_coverage = (
        keywords_hit / len(case["expected_keywords"])
        if case["expected_keywords"]
        else 0.0
    )

    return {
        "id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "expected_route": case["expected_route"],
        "actual_route": actual_route,
        "route_correct": route_correct,
        "keyword_coverage": round(keyword_coverage, 3),
        "confidence_score": result.get("confidence_score", 0.0),
        "escalated": result.get("escalated", False),
        "latency_ms": elapsed_ms,
        "response_preview": result.get("final_response", "")[:150],
    }


def _infer_route_from_agent(agent_used: str) -> str:
    mapping = {
        "knowledge_agent": "knowledge",
        "support_agent": "support",
        "billing_agent": "billing",
        "escalation_agent": "escalation",
    }
    return mapping.get(agent_used, "unknown")


def run_evaluation_suite() -> dict:
    """Run the full golden dataset and compute aggregate metrics."""
    dataset = load_golden_dataset()
    results = [evaluate_single_case(case) for case in dataset]

    n = len(results)
    aggregate = {
        "total_cases": n,
        "routing_accuracy": round(sum(r["route_correct"] for r in results) / n, 3),
        "avg_keyword_coverage": round(
            sum(r["keyword_coverage"] for r in results) / n, 3
        ),
        "avg_confidence": round(sum(r["confidence_score"] for r in results) / n, 3),
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / n, 1),
        "escalation_rate": round(sum(r["escalated"] for r in results) / n, 3),
    }

    return {"aggregate": aggregate, "results": results}


def log_eval_run_to_mlflow(eval_output: dict) -> None:
    """Log the aggregate evaluation metrics + full results as an MLflow run."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(f"{settings.mlflow_experiment_name}-offline-eval")

    with mlflow.start_run(run_name="golden_dataset_eval"):
        for k, v in get_all_prompt_versions().items():
            mlflow.log_param(f"prompt_version_{k}", v)

        for metric_name, value in eval_output["aggregate"].items():
            mlflow.log_metric(metric_name, value)

        mlflow.log_dict(eval_output["results"], "detailed_results.json")
        logger.info("offline_eval_logged", **eval_output["aggregate"])


def main():
    logger.info("starting_offline_evaluation", dataset_path=str(DATASET_PATH))
    eval_output = run_evaluation_suite()

    print("\n=== Offline Evaluation Results ===")
    for k, v in eval_output["aggregate"].items():
        print(f"  {k}: {v}")

    print("\n=== Per-case breakdown ===")
    for r in eval_output["results"]:
        status = "✅" if r["route_correct"] else "❌"
        print(
            f"  {status} [{r['id']}] expected={r['expected_route']} actual={r['actual_route']} "
            f"keyword_coverage={r['keyword_coverage']} latency={r['latency_ms']}ms"
        )

    try:
        log_eval_run_to_mlflow(eval_output)
        print(f"\nLogged to MLflow at {settings.mlflow_tracking_uri}")
    except Exception as e:  # noqa: BLE001
        logger.warning("mlflow_eval_logging_failed", error=str(e))
        print(f"\n[!] Could not log to MLflow (is the server running?): {e}")

    # Exit non-zero if routing accuracy drops below an acceptable bar — useful for CI gating
    if eval_output["aggregate"]["routing_accuracy"] < 0.7:
        print("\n[FAIL] Routing accuracy below 70% threshold — failing CI check.")
        sys.exit(1)


if __name__ == "__main__":
    main()
