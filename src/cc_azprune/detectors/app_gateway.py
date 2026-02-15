"""Detector for orphaned Application Gateways (empty backend pools)."""

from typing import Any

from ..costs import estimate_app_gateway_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type =~ 'microsoft.network/applicationgateways'
| extend backendPoolsCount = array_length(properties.backendAddressPools)
| mvexpand backendPools = properties.backendAddressPools
| extend backendIPCount = array_length(backendPools.properties.backendIPConfigurations)
| extend backendAddressesCount = array_length(backendPools.properties.backendAddresses)
| summarize backendIPCount = sum(backendIPCount), backendAddressesCount = sum(backendAddressesCount) by id, name, resourceGroup, location, subscriptionId, tier = tostring(sku.tier), capacity = toint(sku.capacity)
| where backendIPCount == 0 and backendAddressesCount == 0
"""


def detect_orphaned_app_gateways(query_func) -> list[dict[str, Any]]:
    """Detect Application Gateways with empty backend pools.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Application Gateway resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        tier = item.get("tier", "Standard_v2") or "Standard_v2"
        capacity = item.get("capacity", 2) or 2

        cost = estimate_app_gateway_cost(tier, capacity)

        # Build details
        details_parts = []
        details_parts.append(f"Tier: {tier}")
        details_parts.append(f"Capacity: {capacity}")
        details_parts.append("Empty backend pools")

        resources.append({
            "name": name,
            "type": "microsoft.network/applicationgateways",
            "type_display": "App Gateway",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/applicationgateways"),
        })

    return resources
