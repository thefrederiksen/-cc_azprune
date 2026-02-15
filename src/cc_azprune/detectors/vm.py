"""Detector for stopped/deallocated Virtual Machines."""

from datetime import datetime
from typing import Any

from ..costs import format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == 'microsoft.compute/virtualmachines'
| where properties.extended.instanceView.powerState.displayStatus == 'VM deallocated'
    or properties.extended.instanceView.powerState.code == 'PowerState/deallocated'
| project name, resourceGroup, location, id, subscriptionId,
          vmSize = properties.hardwareProfile.vmSize,
          osType = properties.storageProfile.osDisk.osType,
          timeCreated = properties.timeCreated,
          tags
"""


# Approximate monthly costs for common VM sizes (just the disk/storage portion when deallocated)
# VMs don't charge compute when deallocated, but disks still cost money
VM_SIZE_DISK_COSTS = {
    # B-series (burstable) - typically use smaller disks
    "standard_b1s": 5.0,
    "standard_b1ms": 5.0,
    "standard_b2s": 10.0,
    "standard_b2ms": 10.0,
    "standard_b4ms": 20.0,
    # D-series
    "standard_d2s_v3": 15.0,
    "standard_d4s_v3": 30.0,
    "standard_d2_v3": 15.0,
    "standard_d4_v3": 30.0,
    "standard_ds1_v2": 10.0,
    "standard_ds2_v2": 15.0,
    # General fallback
    "default": 10.0,
}


def estimate_stopped_vm_cost(vm_size: str) -> float:
    """Estimate monthly cost for a stopped VM (disk storage costs).

    Args:
        vm_size: The VM size (e.g., Standard_B2ms)

    Returns:
        Estimated monthly cost for the VM's disks
    """
    size_lower = vm_size.lower() if vm_size else ""

    # Check for exact match first
    if size_lower in VM_SIZE_DISK_COSTS:
        return VM_SIZE_DISK_COSTS[size_lower]

    # Check for partial matches
    for key, cost in VM_SIZE_DISK_COSTS.items():
        if key in size_lower:
            return cost

    return VM_SIZE_DISK_COSTS["default"]


def _format_age(time_created: str | None) -> str:
    """Format creation time as age string."""
    if not time_created:
        return ""

    try:
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


def detect_stopped_vms(query_func) -> list[dict[str, Any]]:
    """Detect stopped/deallocated virtual machines.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of stopped VM resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        vm_size = item.get("vmSize", "") or ""
        os_type = item.get("osType", "")
        time_created = item.get("timeCreated")
        tags = item.get("tags") or {}

        cost = estimate_stopped_vm_cost(vm_size)

        # Build details
        details_parts = []

        # VM size
        if vm_size:
            # Clean up size name for display
            size_display = vm_size.replace("Standard_", "").replace("_", " ")
            details_parts.append(size_display)

        # OS type
        if os_type:
            details_parts.append(os_type)

        # Status
        details_parts.append("Deallocated")

        # Age
        age = _format_age(time_created)
        if age:
            details_parts.append(f"Created {age}")

        # Check tags
        if tags:
            if "purpose" in tags:
                details_parts.insert(0, f"Purpose: {tags['purpose']}")
            elif "environment" in tags:
                details_parts.insert(0, f"Env: {tags['environment']}")

        resources.append({
            "name": name,
            "type": "microsoft.compute/virtualmachines",
            "type_display": "Virtual Machine",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts) if details_parts else "Stopped VM",
            "risk_level": get_risk_level("microsoft.compute/virtualmachines"),
        })

    return resources
