"""Detector for orphaned Virtual Network Gateways (no connections, no VPN clients)."""

from typing import Any

from ..costs import estimate_vnet_gateway_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type =~ "microsoft.network/virtualnetworkgateways"
| extend vpnClientConfiguration = properties.vpnClientConfiguration
| extend sku = sku.name
| extend gatewayType = properties.gatewayType
| join kind=leftouter (
    Resources
    | where type =~ "microsoft.network/connections"
    | mv-expand Resource = pack_array(properties.virtualNetworkGateway1.id, properties.virtualNetworkGateway2.id)
    | project Resource = tostring(Resource), connectionId = id
) on $left.id == $right.Resource
| where isempty(vpnClientConfiguration) and isempty(connectionId)
| project id, name, resourceGroup, location, subscriptionId, sku, gatewayType
"""


def detect_orphaned_vnet_gateways(query_func) -> list[dict[str, Any]]:
    """Detect Virtual Network Gateways with no connections or VPN clients.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned VNet Gateway resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        sku = item.get("sku", "VpnGw1") or "VpnGw1"
        gateway_type = item.get("gatewayType", "Vpn") or "Vpn"

        cost = estimate_vnet_gateway_cost(sku)

        # Build details
        details_parts = []
        details_parts.append(f"Type: {gateway_type}")
        details_parts.append(f"SKU: {sku}")
        details_parts.append("No connections")

        resources.append({
            "name": name,
            "type": "microsoft.network/virtualnetworkgateways",
            "type_display": "VNet Gateway",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/virtualnetworkgateways"),
        })

    return resources
