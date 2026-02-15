"""Detector for orphaned DDoS Protection Plans (no protected VNets)."""

from typing import Any

from ..costs import estimate_ddos_plan_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/ddosprotectionplans"
| where isnull(properties.virtualNetworks) or array_length(properties.virtualNetworks) == 0
| project id, name, resourceGroup, location, subscriptionId,
          provisioningState = properties.provisioningState
"""


def detect_orphaned_ddos_plans(query_func) -> list[dict[str, Any]]:
    """Detect DDoS Protection Plans with no protected virtual networks.

    IMPORTANT: DDoS Protection plans are VERY expensive (~$2,944/month).
    Unused plans should be deleted immediately.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned DDoS Protection Plan resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        state = item.get("provisioningState", "")

        cost = estimate_ddos_plan_cost()

        # Build details
        details_parts = []
        details_parts.append("No protected VNets")
        details_parts.append("HIGH COST")

        if state:
            details_parts.append(f"State: {state}")

        resources.append({
            "name": name,
            "type": "microsoft.network/ddosprotectionplans",
            "type_display": "DDoS Plan",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/ddosprotectionplans"),
        })

    return resources
