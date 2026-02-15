"""Detector for orphaned SQL Elastic Pools (no databases)."""

from typing import Any

from ..costs import estimate_sql_elastic_pool_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type =~ 'microsoft.sql/servers/elasticpools'
| extend poolId = tolower(id)
| join kind=leftouter (
    Resources
    | where type =~ 'Microsoft.Sql/servers/databases'
    | where isnotempty(properties.elasticPoolId)
    | extend elasticPoolId = tolower(tostring(properties.elasticPoolId))
    | project elasticPoolId, databaseId = id
) on $left.poolId == $right.elasticPoolId
| summarize databaseCount = countif(isnotempty(databaseId)) by id, name, resourceGroup, location, subscriptionId, sku = tostring(sku.name), tier = tostring(sku.tier), dtu = toint(properties.dtu)
| where databaseCount == 0
"""


def detect_orphaned_sql_elastic_pools(query_func) -> list[dict[str, Any]]:
    """Detect SQL Elastic Pools with no databases.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned SQL Elastic Pool resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        sku = item.get("sku", "StandardPool") or "StandardPool"
        tier = item.get("tier", "Standard") or "Standard"
        dtu = item.get("dtu", 50) or 50

        cost = estimate_sql_elastic_pool_cost(dtu, tier)

        # Build details
        details_parts = []
        details_parts.append(f"SKU: {sku}")
        details_parts.append(f"Tier: {tier}")
        details_parts.append(f"{dtu} eDTU")
        details_parts.append("No databases")

        resources.append({
            "name": name,
            "type": "microsoft.sql/servers/elasticpools",
            "type_display": "SQL Elastic Pool",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.sql/servers/elasticpools"),
        })

    return resources
