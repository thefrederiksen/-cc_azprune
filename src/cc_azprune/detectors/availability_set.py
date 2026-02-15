"""Detector for orphaned Availability Sets (no VMs)."""

from typing import Any

from ..costs import estimate_availability_set_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.compute/availabilitysets"
| where isnull(properties.virtualMachines) or array_length(properties.virtualMachines) == 0
| project id, name, resourceGroup, location, subscriptionId,
          faultDomains = properties.platformFaultDomainCount,
          updateDomains = properties.platformUpdateDomainCount,
          sku = sku.name
"""


def detect_orphaned_availability_sets(query_func) -> list[dict[str, Any]]:
    """Detect Availability Sets with no VMs.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Availability Set resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        fault_domains = item.get("faultDomains", 2) or 2
        update_domains = item.get("updateDomains", 5) or 5
        sku = item.get("sku", "Classic") or "Classic"

        cost = estimate_availability_set_cost()

        # Build details
        details_parts = []
        details_parts.append(f"SKU: {sku}")
        details_parts.append(f"FD: {fault_domains}")
        details_parts.append(f"UD: {update_domains}")
        details_parts.append("No VMs")

        resources.append({
            "name": name,
            "type": "microsoft.compute/availabilitysets",
            "type_display": "Avail Set",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.compute/availabilitysets"),
        })

    return resources
