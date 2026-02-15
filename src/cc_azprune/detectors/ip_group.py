"""Detector for orphaned IP Groups (no firewall associations)."""

from typing import Any

from ..costs import estimate_ip_group_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/ipgroups"
| where isnull(properties.firewalls) or array_length(properties.firewalls) == 0
| where isnull(properties.firewallPolicies) or array_length(properties.firewallPolicies) == 0
| project id, name, resourceGroup, location, subscriptionId,
          ipAddressCount = array_length(properties.ipAddresses)
"""


def detect_orphaned_ip_groups(query_func) -> list[dict[str, Any]]:
    """Detect IP Groups not associated with any firewalls.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned IP Group resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        ip_count = item.get("ipAddressCount", 0) or 0

        cost = estimate_ip_group_cost()

        # Build details
        details_parts = []

        if ip_count > 0:
            details_parts.append(f"{ip_count} IP(s)")
        else:
            details_parts.append("Empty")

        details_parts.append("No firewall associations")

        resources.append({
            "name": name,
            "type": "microsoft.network/ipgroups",
            "type_display": "IP Group",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/ipgroups"),
        })

    return resources
