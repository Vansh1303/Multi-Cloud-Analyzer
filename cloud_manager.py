"""
Backward-compatibility shim.
All provider implementations now live in providers/ folder.
This file re-exports them so existing imports (dashboard.py, etc.) keep working.
"""
from providers.aws import AWSStorage      # noqa: F401
from providers.azure import AzureStorage  # noqa: F401
from providers.gcp import GCPStorage      # noqa: F401
