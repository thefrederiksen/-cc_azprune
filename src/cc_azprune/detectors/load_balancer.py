"""Detector for orphaned Load Balancers (empty backend pools)."""

from typing import Any

from ..costs import estimate_load_balancer_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/loadbalancers"
| extend backendPools = properties.backendAddressPools
| extend poolCount = array_length(backendPools)
| extend firstPoolIPs = iff(poolCount > 0, array_length(backendPools[0].properties.backendIPConfigurations), 0)
| extend firstPoolAddrs = iff(poolCount > 0, array_length(backendPools[0].properties.loadBalancerBackendAddresses), 0)
| where poolCount == 0 or (firstPoolIPs == 0 and firstPoolAddrs == 0)
| project id, name, resourceGroup, location, subscriptionId,
          sku = sku.name,
          frontendIPCount = array_length(properties.frontendIPConfigurations),
          rulesCount = array_length(properties.loadBalancingRules)
"""


def detect_orphaned_load_balancers(query_func) -> list[dict[str, Any]]:
    """Detect Load Balancers with empty backend pools.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Load Balancer resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        sku = item.get("sku", "Standard") or "Standard"
        frontend_count = item.get("frontendIPCount", 0) or 0
        rules_count = item.get("rulesCount", 0) or 0

        cost = estimate_load_balancer_cost(sku, rules_count)

        # Build details
        details_parts = []
        details_parts.append(f"SKU: {sku}")

        if frontend_count > 0:
            details_parts.append(f"{frontend_count} Frontend IP(s)")

        if rules_count > 0:
            details_parts.append(f"{rules_count} rule(s)")

        details_parts.append("Empty backend")

        resources.append({
            "name": name,
            "type": "microsoft.network/loadbalancers",
            "type_display": "Load Balancer",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/loadbalancers"),
        })

    return resources
