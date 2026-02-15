"""Detector for failed API Connections (Logic Apps connectors in error state)."""

from typing import Any

from ..costs import estimate_api_connection_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.web/connections"
| where properties.statuses[0].status == "Error"
    or properties.statuses[0].status == "Disconnected"
| project id, name, resourceGroup, location, subscriptionId,
          status = properties.statuses[0].status,
          errorMessage = properties.statuses[0].error.message,
          api = properties.api.displayName
"""


def detect_failed_api_connections(query_func) -> list[dict[str, Any]]:
    """Detect API Connections (Logic Apps connectors) in error/disconnected state.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of failed API Connection resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        status = item.get("status", "Error")
        error_msg = item.get("errorMessage", "")
        api_name = item.get("api", "")

        cost = estimate_api_connection_cost()

        # Build details
        details_parts = []

        if api_name:
            details_parts.append(f"API: {api_name}")

        details_parts.append(f"Status: {status}")

        if error_msg and len(error_msg) < 50:
            details_parts.append(error_msg)

        resources.append({
            "name": name,
            "type": "microsoft.web/connections",
            "type_display": "API Connection",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.web/connections"),
        })

    return resources
