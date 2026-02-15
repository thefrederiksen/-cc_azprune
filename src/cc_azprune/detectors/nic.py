"""Detector for orphaned Network Interfaces."""

from typing import Any

from ..costs import estimate_nic_cost, estimate_public_ip_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == 'microsoft.network/networkinterfaces'
| where isnull(properties.virtualMachine)
| project name, resourceGroup, location, id, subscriptionId,
          ipConfigs = properties.ipConfigurations,
          tags
"""


def _extract_vm_name_from_nic(nic_name: str) -> str | None:
    """Try to extract VM name from NIC name.

    Common patterns:
    - {vmname}123 (NIC named after VM with suffix)
    - {vmname}-nic
    - {vmname}VMNic
    """
    # Remove common suffixes
    for suffix in ["-nic", "VMNic", "_nic", "nic"]:
        if nic_name.lower().endswith(suffix.lower()):
            return nic_name[:-len(suffix)]

    # If it ends with numbers, might be VM name
    import re
    match = re.match(r'^(.+?)(\d+)$', nic_name)
    if match and len(match.group(1)) > 3:
        return match.group(1)

    return None


def detect_orphaned_nics(query_func) -> list[dict[str, Any]]:
    """Detect orphaned network interfaces.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned NIC resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        cost = estimate_nic_cost()  # NIC itself is free
        ip_configs = item.get("ipConfigs") or []
        tags = item.get("tags") or {}

        # Build details
        details_parts = []

        # Try to identify original VM
        vm_name = _extract_vm_name_from_nic(name)
        if vm_name:
            details_parts.append(f"VM: {vm_name}")

        # Check for public IP - if present, add its cost since it's wasted
        has_public_ip = False
        for config in ip_configs:
            if config.get("properties", {}).get("publicIPAddress"):
                has_public_ip = True
                break

        if has_public_ip:
            # Add public IP cost since it's attached to orphaned NIC
            public_ip_cost = estimate_public_ip_cost("Standard")  # Assume Standard for safety
            cost += public_ip_cost
            details_parts.append(f"Has Public IP (+${public_ip_cost:.2f}/mo)")
        else:
            details_parts.append("No Public IP")

        # Check tags
        if tags:
            if "vm" in tags:
                details_parts.insert(0, f"VM: {tags['vm']}")
            elif "purpose" in tags:
                details_parts.append(f"Purpose: {tags['purpose']}")

        resources.append({
            "name": name,
            "type": "microsoft.network/networkinterfaces",
            "type_display": "Network Interface",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts) if details_parts else "Orphaned NIC",
            "risk_level": get_risk_level("microsoft.network/networkinterfaces"),
        })

    return resources
