"""Detector for orphaned Network Security Groups (not attached to NIC or subnet)."""

from typing import Any

from ..costs import estimate_nsg_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/networksecuritygroups"
| where isnull(properties.networkInterfaces) or array_length(properties.networkInterfaces) == 0
| where isnull(properties.subnets) or array_length(properties.subnets) == 0
| project id, name, resourceGroup, location, subscriptionId,
          securityRulesCount = array_length(properties.securityRules)
"""


def detect_orphaned_nsgs(query_func) -> list[dict[str, Any]]:
    """Detect Network Security Groups not attached to any NIC or subnet.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned NSG resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        security_rules = item.get("securityRulesCount", 0) or 0

        cost = estimate_nsg_cost()

        # Build details
        details_parts = []

        if security_rules > 0:
            details_parts.append(f"{security_rules} custom rules")
        else:
            details_parts.append("No custom rules")

        details_parts.append("Not attached")

        resources.append({
            "name": name,
            "type": "microsoft.network/networksecuritygroups",
            "type_display": "NSG",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/networksecuritygroups"),
        })

    return resources
