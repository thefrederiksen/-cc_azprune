"""Detector for orphaned Front Door WAF Policies (no security policy links)."""

from typing import Any

from ..costs import estimate_frontdoor_waf_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.network/frontdoorwebapplicationfirewallpolicies"
| where isnull(properties.securityPolicyLinks) or array_length(properties.securityPolicyLinks) == 0
| where isnull(properties.frontendEndpointLinks) or array_length(properties.frontendEndpointLinks) == 0
| project id, name, resourceGroup, location, subscriptionId,
          customRulesCount = array_length(properties.customRules.rules),
          managedRulesCount = array_length(properties.managedRules.managedRuleSets),
          policySettings = properties.policySettings
"""


def detect_orphaned_frontdoor_waf_policies(query_func) -> list[dict[str, Any]]:
    """Detect Front Door WAF Policies not linked to any endpoints.

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of orphaned Front Door WAF Policy resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        custom_rules = item.get("customRulesCount", 0) or 0
        managed_rules = item.get("managedRulesCount", 0) or 0
        settings = item.get("policySettings") or {}

        cost = estimate_frontdoor_waf_cost(rules=custom_rules)

        # Build details
        details_parts = []

        if custom_rules > 0:
            details_parts.append(f"{custom_rules} custom rules")

        if managed_rules > 0:
            details_parts.append(f"{managed_rules} managed rulesets")

        mode = settings.get("mode", "")
        if mode:
            details_parts.append(f"Mode: {mode}")

        details_parts.append("Not linked")

        resources.append({
            "name": name,
            "type": "microsoft.network/frontdoorwebapplicationfirewallpolicies",
            "type_display": "FD WAF Policy",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", "global"),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts),
            "risk_level": get_risk_level("microsoft.network/frontdoorwebapplicationfirewallpolicies"),
        })

    return resources
