"""Detector for orphaned Route Tables (not attached to any subnets)."""

from typing import Any

from ..costs import estimate_route_table_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/routetables"
| where isnull(properties.subnets) or array_length(properties.subnets) == 0
| project id, name, resourceGroup, location, subscriptionId,
          routesCount = array_length(properties.routes),
          disableBgp = properties.disableBgpRoutePropagation
"""


def detect_orphaned_route_tables(query_func) -> list[dict[str, Any]]:
    """Detect Route Tables not attached to any subnets.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Route Table resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        routes_count = item.get("routesCount", 0) or 0
        disable_bgp = item.get("disableBgp", False)

        cost = estimate_route_table_cost()

        # Build details
        details_parts = []

        if routes_count > 0:
            details_parts.append(f"{routes_count} routes")
        else:
            details_parts.append("No routes")

        if disable_bgp:
            details_parts.append("BGP disabled")

        details_parts.append("Not attached")

        resources.append({
            "name": name,
            "type": "microsoft.network/routetables",
            "type_display": "Route Table",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/routetables"),
        })

    return resources
