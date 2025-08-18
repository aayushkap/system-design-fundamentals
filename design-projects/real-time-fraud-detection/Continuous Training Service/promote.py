import time
import os
import getpass
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")


from mlflow.tracking import MlflowClient


def promote_model_to_production(model_name: str, version: int = None, run_id: str = None):
    """
    Promotes a model to production using aliases and demotes any existing production models
    
    Args:
        model_name: Name of the registered model
        version: Model version number to promote
        run_id: Run ID of the model to promote
    """
    client = MlflowClient()
    
    # Resolve version from run_id if needed
    if version is None and run_id is not None:
        versions = client.search_model_versions(f"name='{model_name}' and run_id='{run_id}'")
        if not versions:
            raise ValueError(f"No model version found for run_id {run_id}")
        version = versions[0].version
    
    if version is None:
        raise ValueError("Either version or run_id must be provided")
    
    # Get current production model (if any)
    try:
        current_prod = client.get_model_version_by_alias(model_name, "production")
        if str(current_prod.version) == str(version):
            print(f"Version {version} is already in production")
            return
        client.delete_registered_model_alias(model_name, "production")
        print(f"Removed production alias from version {current_prod.version}")
    except Exception as e:
        if "RESOURCE_DOES_NOT_EXIST" not in str(e):
            raise
        print("No existing production model found")
    
    # Promote new model
    client.set_registered_model_alias(model_name, "production", version)
    print(f"Promoted version {version} to production")

promote_model_to_production(
    run_id="bd21e56013f3410585af4fef941a0fde",
    model_name="m-db6b18d1440d4fb69c75f38d3257ccd7",
)