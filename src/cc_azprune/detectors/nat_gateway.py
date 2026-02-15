"""Detector for orphaned NAT Gateways (not attached to any subnets)."""

from typing import Any

from ..costs import estimate_nat_gateway_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/natgateways"
| where isnull(properties.subnets) or array_length(properties.subnets) == 0
| project id, name, resourceGroup, location, subscriptionId,
          publicIpAddresses = properties.publicIpAddresses,
          publicIpPrefixes = properties.publicIpPrefixes,
          idleTimeoutMinutes = properties.idleTimeoutInMinutes
"""


def detect_orphaned_nat_gateways(query_func) -> list[dict[str, Any]]:
    """Detect NAT Gateways not attached to any subnets.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned NAT Gateway resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        public_ips = item.get("publicIpAddresses") or []
        public_prefixes = item.get("publicIpPrefixes") or []
        idle_timeout = item.get("idleTimeoutMinutes", 4) or 4

        cost = estimate_nat_gateway_cost()

        # Build details
        details_parts = []

        ip_count = len(public_ips)
        prefix_count = len(public_prefixes)
        if ip_count > 0:
            details_parts.append(f"{ip_count} Public IP(s)")
        if prefix_count > 0:
            details_parts.append(f"{prefix_count} IP Prefix(es)")

        details_parts.append(f"Idle: {idle_timeout}min")
        details_parts.append("Not attached to subnet")

        resources.append({
            "name": name,
            "type": "microsoft.network/natgateways",
            "type_display": "NAT Gateway",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/natgateways"),
        })

    return resources
