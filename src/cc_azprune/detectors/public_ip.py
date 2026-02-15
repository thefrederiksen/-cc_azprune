"""Detector for unused Public IP addresses."""

from typing import Any

from ..costs import estimate_public_ip_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == 'microsoft.network/publicipaddresses'
| where isnull(properties.ipConfiguration)
| project name, resourceGroup, location, id, subscriptionId,
          sku = sku.name,
          ipAddress = properties.ipAddress,
          allocationMethod = properties.publicIPAllocationMethod,
          tags
"""


def detect_unused_public_ips(query_func) -> list[dict[str, Any]]:
    """Detect unused public IP addresses.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of unused public IP resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        sku = item.get("sku", "Basic") or "Basic"
        cost = estimate_public_ip_cost(sku)
        ip_address = item.get("ipAddress", "")
        allocation = item.get("allocationMethod", "")
        tags = item.get("tags") or {}

        # Build details
        details_parts = []

        # Show IP if assigned
        if ip_address:
            details_parts.append(f"IP: {ip_address}")

        # SKU affects cost
        details_parts.append(f"SKU: {sku}")

        # Allocation method
        if allocation:
            details_parts.append(allocation)

        # Try to identify what it was for from name
        name_lower = name.lower()
        if "aads" in name_lower or "adds" in name_lower:
            details_parts.insert(0, "Azure AD DS")
        elif "vnet" in name_lower:
            details_parts.insert(0, "VNet related")
        elif "lb" in name_lower or "loadbalancer" in name_lower:
            details_parts.insert(0, "Load Balancer")
        elif "gw" in name_lower or "gateway" in name_lower:
            details_parts.insert(0, "Gateway")

        # Check tags
        if tags:
            if "purpose" in tags:
                details_parts.insert(0, f"Purpose: {tags['purpose']}")
            elif "service" in tags:
                details_parts.insert(0, f"Service: {tags['service']}")

        resources.append({
            "name": name,
            "type": "microsoft.network/publicipaddresses",
            "type_display": "Public IP",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/publicipaddresses"),
        })

    return resources
