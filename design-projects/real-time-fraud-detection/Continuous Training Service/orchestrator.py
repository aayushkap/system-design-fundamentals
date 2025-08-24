# orchestrator.py

from mlflow_train_test import train_and_test
import mlflow
from mlflow.tracking import MlflowClient
import os

import time
import getpass


def orchestrate():
    """Main orchestration function for the ML pipeline"""
    res, run_id = train_and_test()
    
    if res == True and run_id is not None:
        print(f"Training and testing completed successfully. Run ID: {run_id}")
    else:
        print("Training and testing failed or run ID is not available.")

print("Starting orchestration...")
orchestrate()


def promote_run_to_production(run_id: str,
                              model_name: str = "fraud_detector",
                              artifact_path: str = "model",
                              timeout_s: int = 120):
    """
    Minimal promoter: given a run_id, register that run's model (if not already),
    wait until it's READY, then transition it to Production (archiving previous Production).
    Returns the promoted version number (int).

    Requirements:
      - The run must have a logged model at runs:/{run_id}/{artifact_path}
      - MLflow Model Registry must be available (your mlflow server)
    """
    client = MlflowClient()
    model_uri = f"runs:/{run_id}/{artifact_path}"
    promoted_by = os.getenv("USER") or getpass.getuser() or "unknown"

    try:
        existing = client.search_model_versions(f"name='{model_name}'")
    except Exception:
        existing = []

    found_version = None
    for mv in existing:
        mv_run_id = getattr(mv, "run_id", None)
        src = getattr(mv, "source", "") or ""
        if mv_run_id == run_id or f"runs:/{run_id}" in src or run_id in src:
            found_version = str(mv.version)
            break

    # 2) if not found, register the run's model
    if not found_version:
        mv = mlflow.register_model(model_uri, model_name)
        found_version = str(mv.version)

    # 3) wait until model version is READY (or timeout)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = client.get_model_version(model_name, found_version).status
        if status == "READY":
            break
        if status == "FAILED_REGISTRATION":
            raise RuntimeError(f"Registration failed for {model_name} v{found_version}")
        time.sleep(1)
    else:
        raise TimeoutError(f"Timed out waiting for {model_name} v{found_version} to become READY")

    # 4) transition to Production (archive existing productions)
    client.transition_model_version_stage(
        name=model_name,
        version=found_version,
        stage="Production",
        archive_existing_versions=True
    )

    # 5) small metadata tags
    client.set_model_version_tag(model_name, found_version, "promoted_by", promoted_by)
    client.set_model_version_tag(model_name, found_version, "promotion_time", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    return int(found_version)
