"""Cost estimation for Azure resources.

Approximate monthly costs based on Azure pricing.
These are estimates - actual costs vary by region and tier.
"""


def estimate_nic_cost() -> float:
    """NICs are free but may hold public IPs."""
    return 0.0


def estimate_public_ip_cost(sku: str = "Basic") -> float:
    """Estimate monthly cost for public IP.

    Args:
        sku: IP SKU - "Basic" or "Standard"

    Returns:
        Estimated monthly cost in USD
    """
    if sku.lower() == "standard":
        return 4.00
    return 3.65


def estimate_disk_cost(size_gb: int, tier: str = "Standard_LRS") -> float:
    """Estimate monthly cost for managed disk.

    Args:
        size_gb: Disk size in GB
        tier: Storage tier (Standard_LRS, Premium_LRS, etc.)

    Returns:
        Estimated monthly cost in USD
    """
    # Simplified pricing - Standard HDD ~$0.05/GB/month
    # Premium SSD is more expensive but we use conservative estimate
    rate_per_gb = 0.05
    if "premium" in tier.lower():
        rate_per_gb = 0.15
    elif "standardssd" in tier.lower():
        rate_per_gb = 0.075

    return round(size_gb * rate_per_gb, 2)


# =============================================================================
# HIGH COST RESOURCES
# =============================================================================

def estimate_app_gateway_cost(tier: str = "Standard_v2", capacity: int = 2) -> float:
    """Estimate monthly cost for Application Gateway.

    Standard_v2: ~$0.25/hr fixed + $0.008/capacity unit/hr
    WAF_v2: ~$0.36/hr fixed + $0.0144/capacity unit/hr

    Args:
        tier: Gateway tier (Standard_v2, WAF_v2, Standard, WAF)
        capacity: Capacity units (autoscale min or fixed)

    Returns:
        Estimated monthly cost in USD
    """
    hours_per_month = 730

    if "waf" in tier.lower():
        fixed_rate = 0.36
        capacity_rate = 0.0144
    else:
        fixed_rate = 0.25
        capacity_rate = 0.008

    fixed_cost = fixed_rate * hours_per_month
    capacity_cost = capacity_rate * capacity * hours_per_month

    return round(fixed_cost + capacity_cost, 2)


def estimate_vnet_gateway_cost(sku: str = "VpnGw1") -> float:
    """Estimate monthly cost for Virtual Network Gateway.

    Args:
        sku: Gateway SKU (Basic, VpnGw1, VpnGw2, VpnGw3, VpnGw4, VpnGw5,
             ErGw1AZ, ErGw2AZ, ErGw3AZ)

    Returns:
        Estimated monthly cost in USD
    """
    # Approximate monthly costs by SKU
    sku_costs = {
        "basic": 27.00,
        "vpngw1": 140.00,
        "vpngw1az": 196.00,
        "vpngw2": 361.00,
        "vpngw2az": 506.00,
        "vpngw3": 927.00,
        "vpngw3az": 1298.00,
        "vpngw4": 1825.00,
        "vpngw4az": 2555.00,
        "vpngw5": 3650.00,
        "vpngw5az": 5110.00,
        # ExpressRoute
        "ergw1az": 214.00,
        "ergw2az": 536.00,
        "ergw3az": 1072.00,
        "standard": 214.00,  # ER Standard
        "highperformance": 536.00,  # ER High Performance
        "ultrahighperformance": 1072.00,  # ER Ultra
    }

    sku_lower = sku.lower().replace("-", "").replace("_", "")
    return sku_costs.get(sku_lower, 140.00)


def estimate_nat_gateway_cost(data_processed_gb: float = 0) -> float:
    """Estimate monthly cost for NAT Gateway.

    NAT Gateway: $0.045/hr + $0.045/GB processed

    Args:
        data_processed_gb: Data processed in GB (0 if unknown)

    Returns:
        Estimated monthly cost in USD
    """
    hours_per_month = 730
    hourly_cost = 0.045 * hours_per_month  # ~$32.85/month fixed
    data_cost = 0.045 * data_processed_gb

    return round(hourly_cost + data_cost, 2)


def estimate_load_balancer_cost(sku: str = "Standard", rules: int = 5) -> float:
    """Estimate monthly cost for Load Balancer.

    Basic: Free
    Standard: $0.025/hr + $0.005/rule/hr (first 5 rules free)

    Args:
        sku: Load balancer SKU (Basic, Standard)
        rules: Number of load balancing rules

    Returns:
        Estimated monthly cost in USD
    """
    if sku.lower() == "basic":
        return 0.0

    hours_per_month = 730
    base_cost = 0.025 * hours_per_month  # ~$18.25/month

    # First 5 rules free, then $0.005/rule/hr
    extra_rules = max(0, rules - 5)
    rules_cost = 0.005 * extra_rules * hours_per_month

    return round(base_cost + rules_cost, 2)


def estimate_sql_elastic_pool_cost(dtu: int = 50, tier: str = "Standard") -> float:
    """Estimate monthly cost for SQL Elastic Pool.

    Args:
        dtu: eDTUs provisioned
        tier: Service tier (Basic, Standard, Premium)

    Returns:
        Estimated monthly cost in USD
    """
    # Approximate per-eDTU monthly costs by tier
    tier_rates = {
        "basic": 0.0075,
        "standard": 0.0225,
        "premium": 0.075,
    }

    rate = tier_rates.get(tier.lower(), 0.0225)
    hours_per_month = 730

    return round(dtu * rate * hours_per_month, 2)


def estimate_app_service_plan_cost(tier: str = "Basic", size: str = "B1") -> float:
    """Estimate monthly cost for App Service Plan.

    Args:
        tier: Service tier (Free, Shared, Basic, Standard, Premium, PremiumV2, PremiumV3)
        size: Size within tier (B1, B2, B3, S1, S2, S3, P1v2, etc.)

    Returns:
        Estimated monthly cost in USD
    """
    # Approximate monthly costs by SKU
    sku_costs = {
        # Free and Shared
        "f1": 0.0,
        "free": 0.0,
        "d1": 10.0,
        "shared": 10.0,
        # Basic
        "b1": 55.0,
        "b2": 109.0,
        "b3": 219.0,
        # Standard
        "s1": 73.0,
        "s2": 146.0,
        "s3": 292.0,
        # Premium
        "p1": 146.0,
        "p2": 292.0,
        "p3": 584.0,
        # Premium v2
        "p1v2": 88.0,
        "p2v2": 175.0,
        "p3v2": 350.0,
        # Premium v3
        "p1v3": 104.0,
        "p2v3": 208.0,
        "p3v3": 416.0,
    }

    size_lower = size.lower().replace("_", "").replace("-", "")
    return sku_costs.get(size_lower, 73.0)  # Default to S1


# =============================================================================
# MEDIUM COST RESOURCES
# =============================================================================

def estimate_ddos_plan_cost() -> float:
    """Estimate monthly cost for DDoS Protection Plan.

    DDoS Protection Standard is expensive: ~$2,944/month fixed
    Plus overage charges for protected resources

    Returns:
        Estimated monthly cost in USD (fixed portion only)
    """
    return 2944.00


def estimate_traffic_manager_cost(endpoints: int = 2, queries_millions: float = 1) -> float:
    """Estimate monthly cost for Traffic Manager Profile.

    $0.54/million queries + $0.36/endpoint/month (Azure endpoints)
    External endpoints: $0.54/endpoint/month

    Args:
        endpoints: Number of endpoints
        queries_millions: DNS queries in millions

    Returns:
        Estimated monthly cost in USD
    """
    query_cost = 0.54 * queries_millions
    endpoint_cost = 0.36 * endpoints

    return round(query_cost + endpoint_cost, 2)


def estimate_frontdoor_waf_cost(rules: int = 10) -> float:
    """Estimate monthly cost for Front Door WAF Policy.

    $5/month per policy + $1/month per custom rule

    Args:
        rules: Number of custom rules

    Returns:
        Estimated monthly cost in USD
    """
    policy_cost = 5.0
    rules_cost = 1.0 * rules

    return round(policy_cost + rules_cost, 2)


# =============================================================================
# LOW/NO COST RESOURCES (cleanup value, not cost savings)
# =============================================================================

def estimate_nsg_cost() -> float:
    """NSGs are free."""
    return 0.0


def estimate_route_table_cost() -> float:
    """Route tables are free."""
    return 0.0


def estimate_availability_set_cost() -> float:
    """Availability sets are free."""
    return 0.0


def estimate_vnet_cost() -> float:
    """Virtual networks are free."""
    return 0.0


def estimate_subnet_cost() -> float:
    """Subnets are free."""
    return 0.0


def estimate_ip_group_cost() -> float:
    """IP Groups are free."""
    return 0.0


def estimate_private_dns_zone_cost(records: int = 0) -> float:
    """Estimate monthly cost for Private DNS Zone.

    First zone free, then $0.50/zone/month
    $0.40 per million queries

    Args:
        records: Number of records (not used in estimate)

    Returns:
        Estimated monthly cost in USD
    """
    return 0.50  # Per zone cost


def estimate_private_endpoint_cost() -> float:
    """Estimate monthly cost for Private Endpoint.

    $0.01/hr + data processing fees

    Returns:
        Estimated monthly cost in USD
    """
    return round(0.01 * 730, 2)  # ~$7.30/month


def estimate_resource_group_cost() -> float:
    """Resource groups are free."""
    return 0.0


def estimate_api_connection_cost() -> float:
    """API connections (Logic Apps connectors) are free.

    The cost is in the Logic App runs, not the connection itself.
    """
    return 0.0


def estimate_certificate_cost() -> float:
    """App Service Certificates themselves are free (one-time purchase).

    Expired certificates have no recurring cost but represent security risk.
    """
    return 0.0


# =============================================================================
# UTILITY
# =============================================================================

def format_cost(cost: float) -> str:
    """Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string like "$3.65" or "$0"
    """
    if cost == 0:
        return "$0"
    elif cost >= 1000:
        return f"${cost:,.0f}"
    elif cost >= 100:
        return f"${cost:.0f}"
    else:
        return f"${cost:.2f}"


# Cost priority categories for sorting/filtering
COST_PRIORITY = {
    "ddos_plan": 1,  # ~$2,944/mo - VERY HIGH
    "vnet_gateway": 1,  # $130-1000+
    "app_gateway": 1,  # $150-500+
    "sql_elastic_pool": 1,  # $150+
    "app_service_plan": 1,  # $50-400+
    "nat_gateway": 2,  # ~$32+
    "load_balancer": 2,  # ~$18+
    "disk": 2,  # $2-150+
    "private_endpoint": 3,  # ~$7
    "public_ip": 3,  # ~$4
    "traffic_manager": 3,  # $1-10
    "frontdoor_waf": 3,  # ~$5+
    "private_dns_zone": 3,  # ~$0.50
    "vm": 3,  # Disk costs only when stopped
    "nic": 4,  # Free
    "nsg": 4,  # Free
    "route_table": 4,  # Free
    "availability_set": 4,  # Free
    "vnet": 4,  # Free
    "subnet": 4,  # Free
    "ip_group": 4,  # Free
    "resource_group": 4,  # Free
    "api_connection": 4,  # Free
    "certificate": 4,  # Free (security concern)
}
