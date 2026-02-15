"""Detector for orphaned Traffic Manager Profiles (no endpoints)."""

from typing import Any

from ..costs import estimate_traffic_manager_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/trafficmanagerprofiles"
| where isnull(properties.endpoints) or array_length(properties.endpoints) == 0
| project id, name, resourceGroup, location, subscriptionId,
          trafficRoutingMethod = properties.trafficRoutingMethod,
          profileStatus = properties.profileStatus,
          dnsName = properties.dnsConfig.relativeName
"""


def detect_orphaned_traffic_managers(query_func) -> list[dict[str, Any]]:
    """Detect Traffic Manager Profiles with no endpoints.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Traffic Manager Profile resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        routing_method = item.get("trafficRoutingMethod", "")
        status = item.get("profileStatus", "")
        dns_name = item.get("dnsName", "")

        # Minimal cost estimate with 0 endpoints
        cost = estimate_traffic_manager_cost(endpoints=0, queries_millions=0)

        # Build details
        details_parts = []

        if routing_method:
            details_parts.append(f"Routing: {routing_method}")

        if status:
            details_parts.append(f"Status: {status}")

        if dns_name:
            details_parts.append(f"DNS: {dns_name}")

        details_parts.append("No endpoints")

        resources.append({
            "name": name,
            "type": "microsoft.network/trafficmanagerprofiles",
            "type_display": "Traffic Manager",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", "global"),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/trafficmanagerprofiles"),
        })

    return resources
