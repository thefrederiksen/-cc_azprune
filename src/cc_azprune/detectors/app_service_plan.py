"""Detector for orphaned App Service Plans (no apps hosted)."""

from typing import Any

from ..costs import estimate_app_service_plan_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type =~ "microsoft.web/serverfarms"
| where properties.numberOfSites == 0
| project id, name, resourceGroup, location, subscriptionId,
          sku = sku.name,
          tier = sku.tier,
          size = sku.size,
          capacity = sku.capacity,
          kind = kind
"""


def detect_orphaned_app_service_plans(query_func) -> list[dict[str, Any]]:
    """Detect App Service Plans with no apps hosted.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned App Service Plan resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        sku = item.get("sku", "B1") or "B1"
        tier = item.get("tier", "Basic") or "Basic"
        size = item.get("size", "B1") or "B1"
        capacity = item.get("capacity", 1) or 1
        kind = item.get("kind", "") or ""

        cost = estimate_app_service_plan_cost(tier, size)
        # Multiply by instance count
        cost = cost * capacity

        # Build details
        details_parts = []

        # Kind interpretation
        if "linux" in kind.lower():
            details_parts.append("Linux")
        elif "windows" in kind.lower():
            details_parts.append("Windows")
        elif "functionapp" in kind.lower():
            details_parts.append("Functions")

        details_parts.append(f"SKU: {sku}")

        if capacity > 1:
            details_parts.append(f"{capacity} instances")

        details_parts.append("No apps")

        resources.append({
            "name": name,
            "type": "microsoft.web/serverfarms",
            "type_display": "App Service Plan",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.web/serverfarms"),
        })

    return resources
