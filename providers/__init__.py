import os

# Registry: key -> (module_path, class_name, required_env_vars)
# Lazy-loaded to avoid import crashes when a provider's SDK isn't installed
PROVIDER_REGISTRY = {
    "aws": {
        "name": "AWS",
        "module": "providers.aws",
        "class": "AWSStorage",
        "env_keys": ["AWS_ACCESS_KEY_ID", "AWS_BUCKET_NAME"],
        "bucket_env": "AWS_BUCKET_NAME",
    },
    "azure": {
        "name": "Azure",
        "module": "providers.azure",
        "class": "AzureStorage",
        "env_keys": ["AZURE_STORAGE_CONNECTION_STRING", "AZURE_CONTAINER_NAME"],
        "bucket_env": "AZURE_CONTAINER_NAME",
    },
    "gcp": {
        "name": "GCP",
        "module": "providers.gcp",
        "class": "GCPStorage",
        "env_keys": ["GCP_PROJECT_ID", "GCP_BUCKET_NAME"],
        "bucket_env": "GCP_BUCKET_NAME",
    },
}


def check_provider_env(key):
    """Return (is_ready, first_missing_var) for a provider."""
    info = PROVIDER_REGISTRY[key]
    for env_key in info["env_keys"]:
        if not os.getenv(env_key):
            return False, env_key
    return True, None


def load_provider(key):
    """Lazily import and instantiate a provider. Returns (client, bucket) or None."""
    import importlib
    info = PROVIDER_REGISTRY[key]
    ok, missing = check_provider_env(key)
    if not ok:
        print(f"  Cannot use {info['name']}: missing {missing} in .env")
        return None
    try:
        mod = importlib.import_module(info["module"])
        cls = getattr(mod, info["class"])
        client = cls()
        bucket = os.getenv(info["bucket_env"])
        return client, bucket
    except Exception as e:
        print(f"  {info['name']} init failed: {e}")
        return None
