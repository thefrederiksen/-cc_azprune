"""Detector for unattached Managed Disks."""

import re
from datetime import datetime
from typing import Any

from ..costs import estimate_disk_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == 'microsoft.compute/disks'
| where isnull(properties.managedBy)
| where properties.diskState != 'ActiveSAS'
| project name, resourceGroup, location, id, subscriptionId,
          diskSizeGB = properties.diskSizeGB,
          sku = sku.name,
          timeCreated = properties.timeCreated,
          tags
"""


def _extract_vm_name(disk_name: str) -> str | None:
    """Try to extract the original VM name from a disk name.

    Azure typically names disks like:
    - {vmname}_OsDisk_1_{guid}
    - {vmname}_DataDisk_{lun}_{guid}
    - {vmname}-osdisk
    """
    # Pattern: vmname_OsDisk_1_guid or vmname_DataDisk_0_guid
    match = re.match(r'^(.+?)_(Os|Data)Disk_\d+_', disk_name, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern: vmname-osdisk or vmname-datadisk
    match = re.match(r'^(.+?)-(os|data)disk', disk_name, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def _format_age(time_created: str | None) -> str:
    """Format creation time as age string."""
    if not time_created:
        return ""

    try:
        # Parse ISO format
        created = datetime.fromisoformat(time_created.replace("Z", "+00:00"))
        now = datetime.now(created.tzinfo)
        delta = now - created

        days = delta.days
        if days < 1:
            return "today"
        elif days == 1:
            return "1 day ago"
        elif days < 30:
            return f"{days} days ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    except Exception:
        return ""


def detect_unattached_disks(query_func) -> list[dict[str, Any]]:
    """Detect unattached managed disks.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of unattached disk resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        size_gb = item.get("diskSizeGB", 0) or 0
        sku = item.get("sku", "Standard_LRS") or "Standard_LRS"
        cost = estimate_disk_cost(size_gb, sku)
        time_created = item.get("timeCreated")
        tags = item.get("tags") or {}

        # Build details string
        details_parts = []

        # Try to identify original VM
        vm_name = _extract_vm_name(name)
        if vm_name:
            details_parts.append(f"VM: {vm_name}")

        # Add size
        details_parts.append(f"{size_gb} GB")

        # Add age
        age = _format_age(time_created)
        if age:
            details_parts.append(f"Created {age}")

        # Check for useful tags
        if tags:
            if "purpose" in tags:
                details_parts.append(f"Purpose: {tags['purpose']}")
            elif "application" in tags:
                details_parts.append(f"App: {tags['application']}")
            elif "environment" in tags:
                details_parts.append(f"Env: {tags['environment']}")

        resources.append({
            "name": name,
            "type": "microsoft.compute/disks",
            "type_display": "Managed Disk",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.compute/disks"),
        })

    return resources
