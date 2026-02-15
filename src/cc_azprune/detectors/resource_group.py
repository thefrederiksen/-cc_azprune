"""Detector for empty Resource Groups."""

from typing import Any

from ..costs import estimate_resource_group_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
ResourceContainers
| where type == "microsoft.resources/subscriptions/resourcegroups"
| join kind=leftouter (
    Resources
    | summarize resourceCount = count() by resourceGroup, subscriptionId
) on $left.name == $right.resourceGroup and $left.subscriptionId == $right.subscriptionId
| where isnull(resourceCount) or resourceCount == 0
| project id, name, location, subscriptionId, tags
"""


def detect_empty_resource_groups(query_func) -> list[dict[str, Any]]:
    """Detect empty Resource Groups with no resources.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of empty Resource Group resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        tags = item.get("tags") or {}

        cost = estimate_resource_group_cost()

        # Build details
        details_parts = []
        details_parts.append("Empty")

        # Check for meaningful tags
        if tags:
            if "environment" in tags:
                details_parts.insert(0, f"Env: {tags['environment']}")
            elif "purpose" in tags:
                details_parts.insert(0, f"Purpose: {tags['purpose']}")
            elif "owner" in tags:
                details_parts.insert(0, f"Owner: {tags['owner']}")

        resources.append({
            "name": name,
            "type": "microsoft.resources/subscriptions/resourcegroups",
            "type_display": "Resource Group",
            "resource_group": name,  # RG is itself
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.resources/subscriptions/resourcegroups"),
        })

    return resources
