"""Detector for orphaned Private DNS Zones (no VNet links)."""

from typing import Any

from ..costs import estimate_private_dns_zone_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/privatednszones"
| where isnull(properties.numberOfVirtualNetworkLinks) or properties.numberOfVirtualNetworkLinks == 0
| project id, name, resourceGroup, location, subscriptionId,
          recordCount = properties.numberOfRecordSets,
          maxRecords = properties.maxNumberOfRecordSets
"""


def detect_orphaned_private_dns_zones(query_func) -> list[dict[str, Any]]:
    """Detect Private DNS Zones with no VNet links.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Private DNS Zone resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        record_count = item.get("recordCount", 0) or 0

        cost = estimate_private_dns_zone_cost()

        # Build details
        details_parts = []

        if record_count > 0:
            details_parts.append(f"{record_count} records")
        else:
            details_parts.append("No records")

        details_parts.append("No VNet links")

        resources.append({
            "name": name,
            "type": "microsoft.network/privatednszones",
            "type_display": "Private DNS",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", "global"),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/privatednszones"),
        })

    return resources
