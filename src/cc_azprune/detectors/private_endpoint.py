"""Detector for orphaned Private Endpoints (disconnected state)."""

from typing import Any

from ..costs import estimate_private_endpoint_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/privateendpoints"
| mv-expand connection = properties.privateLinkServiceConnections
| mv-expand manualConnection = properties.manualPrivateLinkServiceConnections
| extend connState = coalesce(
    tostring(connection.properties.privateLinkServiceConnectionState.status),
    tostring(manualConnection.properties.privateLinkServiceConnectionState.status)
)
| where connState == "Disconnected" or connState == "Rejected"
| project id, name, resourceGroup, location, subscriptionId,
          connectionState = connState,
          subnet = tostring(split(properties.subnet.id, "/")[-1])
"""


def detect_orphaned_private_endpoints(query_func) -> list[dict[str, Any]]:
    """Detect Private Endpoints in disconnected or rejected state.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Private Endpoint resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        conn_state = item.get("connectionState", "Disconnected")
        subnet = item.get("subnet", "")

        cost = estimate_private_endpoint_cost()

        # Build details
        details_parts = []
        details_parts.append(f"State: {conn_state}")

        if subnet:
            details_parts.append(f"Subnet: {subnet}")

        resources.append({
            "name": name,
            "type": "microsoft.network/privateendpoints",
            "type_display": "Private Endpoint",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/privateendpoints"),
        })

    return resources
