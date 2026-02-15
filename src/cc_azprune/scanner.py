"""Azure Resource Graph scanner."""

import json
import os
import subprocess
import traceback
from pathlib import Path
from typing import Any, Callable

from azure.identity import AzureCliCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

from .logging_config import get_logger
from .detectors import ALL_DETECTORS

log = get_logger("scanner")


def find_azure_cli() -> str | None:
    """Find Azure CLI executable path.

    Checks PATH first, then common installation locations on Windows.

    Returns:
        Path to az.cmd or None if not found
    """
    # First, check if 'az' is in PATH
    log.debug("Searching for Azure CLI...")

    # Try common commands
    for cmd in ["az.cmd", "az"]:
        try:
            result = subprocess.run(
                ["where", cmd],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split('\n')[0]
                log.debug(f"Found Azure CLI via 'where': {path}")
                return path
        except Exception:
            pass

    # Check common Windows installation paths
    common_paths = [
        # Per-user installation (most common)
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft SDKs" / "Azure" / "CLI2" / "wbin" / "az.cmd",
        # All-users installation
        Path("C:/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az.cmd"),
        Path("C:/Program Files (x86)/Microsoft SDKs/Azure/CLI2/wbin/az.cmd"),
    ]

    for path in common_paths:
        if path.exists():
            log.debug(f"Found Azure CLI at: {path}")
            return str(path)

    log.debug("Azure CLI not found in any known location")
    return None


class AzureScanner:
    """Scanner for orphaned Azure resources."""

    def __init__(self):
        """Initialize scanner with Azure CLI credentials."""
        log.debug("Initializing AzureScanner")
        self.credential: AzureCliCredential | None = None
        self.subscription_id: str | None = None
        self.subscription_name: str | None = None
        self.tenant_id: str | None = None
        self._rg_client: ResourceGraphClient | None = None

    def authenticate(self) -> bool:
        """Check Azure CLI authentication and get subscription info.

        Returns:
            True if authenticated successfully

        Raises:
            Exception: If not authenticated or no subscription found
        """
        log.info("Starting authentication...")

        # Step 1: Find Azure CLI
        log.debug("Step 1: Finding Azure CLI installation")
        az_path = find_azure_cli()

        if not az_path:
            log.error("Azure CLI not found in PATH or common installation locations")
            raise Exception("Azure CLI not found. Please install it from: https://aka.ms/installazurecli")

        log.info(f"Using Azure CLI at: {az_path}")

        # Step 2: Check Azure CLI works
        log.debug("Step 2: Verifying Azure CLI works")
        try:
            result = subprocess.run(
                [az_path, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            if result.returncode == 0:
                # Extract version from first line
                version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
                log.info(f"Azure CLI version: {version_line}")
            else:
                log.error(f"Azure CLI check failed: {result.stderr}")
                raise Exception("Azure CLI not working properly. Please reinstall from: https://aka.ms/installazurecli")
        except subprocess.TimeoutExpired:
            log.error("Azure CLI version check timed out after 30 seconds")
            raise Exception("Azure CLI is not responding. Try restarting your terminal.")

        # Step 3: Get the default subscription from Azure CLI
        log.debug("Step 3: Getting default subscription via 'az account show'")
        try:
            result = subprocess.run(
                [az_path, "account", "show", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )

            log.debug(f"az account show returncode: {result.returncode}")

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                log.error(f"az account show failed: {error_msg}")

                if "az login" in error_msg.lower() or "please run" in error_msg.lower():
                    raise Exception("Not logged in to Azure. Run 'az login' in a terminal first.")
                if "no subscription" in error_msg.lower():
                    raise Exception("No Azure subscription found. Ensure your account has access to a subscription.")
                raise Exception(f"Azure CLI error: {error_msg}")

            log.debug(f"az account show stdout length: {len(result.stdout)} chars")

            account = json.loads(result.stdout)
            self.subscription_id = account.get("id")
            self.subscription_name = account.get("name")
            self.tenant_id = account.get("tenantId")

            log.info(f"Subscription: {self.subscription_name}")
            log.info(f"Subscription ID: {self.subscription_id}")
            log.info(f"Tenant ID: {self.tenant_id}")

            if not self.subscription_id:
                log.error("No subscription ID in account data")
                raise Exception("No subscription found. Run 'az login' first.")

        except subprocess.TimeoutExpired:
            log.error("az account show timed out after 30 seconds")
            raise Exception("Azure CLI is not responding. Your session may have expired. Run 'az login' again.")
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON from az account show: {e}")
            log.debug(f"Raw output: {result.stdout[:500] if result.stdout else 'empty'}")
            raise Exception("Could not parse Azure CLI output. Try running 'az login' again.")

        # Step 3: Initialize Azure credential and Resource Graph client
        log.debug("Step 3: Initializing Azure credentials")
        try:
            self.credential = AzureCliCredential()
            log.debug("AzureCliCredential created")

            self._rg_client = ResourceGraphClient(self.credential)
            log.debug("ResourceGraphClient created")

        except Exception as e:
            log.error(f"Failed to create Azure clients: {e}")
            log.debug(traceback.format_exc())
            raise Exception(f"Failed to initialize Azure connection: {e}")

        log.info("Authentication successful")
        return True

    def list_subscriptions(self) -> list[dict[str, str]]:
        """List all available Azure subscriptions.

        Returns:
            List of subscription dictionaries with 'id', 'name', and 'isDefault' keys
        """
        log.debug("Listing available subscriptions")

        az_path = find_azure_cli()
        if not az_path:
            log.error("Azure CLI not found")
            return []

        try:
            result = subprocess.run(
                [az_path, "account", "list", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )

            if result.returncode != 0:
                log.error(f"az account list failed: {result.stderr}")
                return []

            subscriptions = json.loads(result.stdout)
            log.info(f"Found {len(subscriptions)} subscriptions")

            return [
                {
                    "id": sub.get("id", ""),
                    "name": sub.get("name", ""),
                    "isDefault": sub.get("isDefault", False),
                    "tenantId": sub.get("tenantId", ""),
                }
                for sub in subscriptions
                if sub.get("state") == "Enabled"
            ]

        except subprocess.TimeoutExpired:
            log.error("az account list timed out")
            return []
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse subscriptions JSON: {e}")
            return []
        except Exception as e:
            log.error(f"Failed to list subscriptions: {e}")
            return []

    def set_subscription(self, subscription_id: str, subscription_name: str, tenant_id: str) -> bool:
        """Set the active subscription for scanning.

        Args:
            subscription_id: Azure subscription ID
            subscription_name: Display name of subscription
            tenant_id: Azure tenant ID

        Returns:
            True if set successfully
        """
        log.info(f"Setting subscription to: {subscription_name}")
        self.subscription_id = subscription_id
        self.subscription_name = subscription_name
        self.tenant_id = tenant_id
        return True

    def _query(self, query: str) -> list[dict[str, Any]]:
        """Execute Resource Graph query.

        Args:
            query: Kusto query string

        Returns:
            List of result dictionaries
        """
        if not self._rg_client or not self.subscription_id:
            log.error("_query called but not authenticated")
            raise Exception("Not authenticated. Call authenticate() first.")

        log.debug(f"Executing query: {query[:100]}...")

        try:
            request = QueryRequest(
                subscriptions=[self.subscription_id],
                query=query,
            )

            response = self._rg_client.resources(request)
            result_count = len(response.data) if response.data else 0
            log.debug(f"Query returned {result_count} results")

            return response.data or []

        except Exception as e:
            log.error(f"Query failed: {e}")
            log.debug(traceback.format_exc())
            raise

    def scan(self, progress_callback: Callable[[str], None] | None = None) -> list[dict[str, Any]]:
        """Scan for all orphaned resources.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            List of all orphaned resources
        """
        log.info("Starting comprehensive scan for orphaned resources")
        all_resources = []

        def update_progress(msg: str):
            log.info(msg)
            if progress_callback:
                progress_callback(msg)

        try:
            for resource_name, detector_func in ALL_DETECTORS:
                update_progress(f"Scanning {resource_name}...")
                try:
                    results = detector_func(self._query)
                    # Ensure results is a list (handle None)
                    if results is None:
                        results = []
                    count = len(results)
                    log.info(f"Found {count} orphaned {resource_name}")
                    all_resources.extend(results)
                except Exception as e:
                    log.warning(f"Detector {resource_name} failed: {e}")
                    # Continue with other detectors

            update_progress(f"Scan complete. Found {len(all_resources)} orphaned resources.")
            log.info(f"Total orphaned resources: {len(all_resources)}")

        except Exception as e:
            log.error(f"Scan failed: {e}")
            log.debug(traceback.format_exc())
            raise

        return all_resources
