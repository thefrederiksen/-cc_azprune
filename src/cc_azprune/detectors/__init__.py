"""Resource detectors for identifying orphaned Azure resources.

This module provides detection functions for 20+ resource types organized by cost impact:

HIGH COST (Priority 1 - $50-3000+/month):
- Application Gateways (empty backend pools)
- Virtual Network Gateways (no connections)
- NAT Gateways (not attached to subnets)
- Load Balancers (empty backend pools)
- SQL Elastic Pools (no databases)
- App Service Plans (no apps)
- DDoS Protection Plans (no protected VNets) - VERY EXPENSIVE

MEDIUM COST (Priority 2 - $5-50/month):
- Unattached Managed Disks
- Unused Public IPs
- Traffic Manager Profiles (no endpoints)
- Front Door WAF Policies (not linked)
- Private Endpoints (disconnected)

LOW/NO COST (Priority 3 - cleanup/security value):
- Stopped/Deallocated VMs (disk costs only)
- Orphaned Network Interfaces
- Network Security Groups (not attached)
- Route Tables (not attached)
- Availability Sets (no VMs)
- IP Groups (no firewall associations)
- Private DNS Zones (no VNet links)
- Empty Resource Groups
- Failed API Connections
- Expired Certificates
"""

# Existing detectors
from .nic import detect_orphaned_nics
from .disk import detect_unattached_disks
from .public_ip import detect_unused_public_ips
from .vm import detect_stopped_vms

# High-cost detectors (Priority 1)
from .app_gateway import detect_orphaned_app_gateways
from .vnet_gateway import detect_orphaned_vnet_gateways
from .nat_gateway import detect_orphaned_nat_gateways
from .load_balancer import detect_orphaned_load_balancers
from .sql_elastic_pool import detect_orphaned_sql_elastic_pools
from .app_service_plan import detect_orphaned_app_service_plans

# Medium-cost detectors (Priority 2)
from .ddos_plan import detect_orphaned_ddos_plans
from .traffic_manager import detect_orphaned_traffic_managers
from .frontdoor_waf import detect_orphaned_frontdoor_waf_policies

# Low/no-cost detectors (Priority 3)
from .nsg import detect_orphaned_nsgs
from .route_table import detect_orphaned_route_tables
from .availability_set import detect_orphaned_availability_sets
from .ip_group import detect_orphaned_ip_groups
from .private_dns import detect_orphaned_private_dns_zones
from .private_endpoint import detect_orphaned_private_endpoints
from .resource_group import detect_empty_resource_groups
from .api_connection import detect_failed_api_connections
from .certificate import detect_expired_certificates


# All detectors organized by priority (highest cost first)
ALL_DETECTORS = [
    # Priority 1: High cost
    ("DDoS Protection Plans", detect_orphaned_ddos_plans),
    ("Application Gateways", detect_orphaned_app_gateways),
    ("VNet Gateways", detect_orphaned_vnet_gateways),
    ("SQL Elastic Pools", detect_orphaned_sql_elastic_pools),
    ("App Service Plans", detect_orphaned_app_service_plans),
    ("NAT Gateways", detect_orphaned_nat_gateways),
    ("Load Balancers", detect_orphaned_load_balancers),
    # Priority 2: Medium cost
    ("Managed Disks", detect_unattached_disks),
    ("Public IPs", detect_unused_public_ips),
    ("Traffic Manager Profiles", detect_orphaned_traffic_managers),
    ("Front Door WAF Policies", detect_orphaned_frontdoor_waf_policies),
    ("Private Endpoints", detect_orphaned_private_endpoints),
    # Priority 3: Low/no cost (cleanup value)
    ("Stopped VMs", detect_stopped_vms),
    ("Network Interfaces", detect_orphaned_nics),
    ("Network Security Groups", detect_orphaned_nsgs),
    ("Route Tables", detect_orphaned_route_tables),
    ("Availability Sets", detect_orphaned_availability_sets),
    ("IP Groups", detect_orphaned_ip_groups),
    ("Private DNS Zones", detect_orphaned_private_dns_zones),
    ("Resource Groups", detect_empty_resource_groups),
    ("API Connections", detect_failed_api_connections),
    ("Certificates", detect_expired_certificates),
]


__all__ = [
    # Original detectors
    "detect_orphaned_nics",
    "detect_unattached_disks",
    "detect_unused_public_ips",
    "detect_stopped_vms",
    # High-cost detectors
    "detect_orphaned_app_gateways",
    "detect_orphaned_vnet_gateways",
    "detect_orphaned_nat_gateways",
    "detect_orphaned_load_balancers",
    "detect_orphaned_sql_elastic_pools",
    "detect_orphaned_app_service_plans",
    # Medium-cost detectors
    "detect_orphaned_ddos_plans",
    "detect_orphaned_traffic_managers",
    "detect_orphaned_frontdoor_waf_policies",
    # Low/no-cost detectors
    "detect_orphaned_nsgs",
    "detect_orphaned_route_tables",
    "detect_orphaned_availability_sets",
    "detect_orphaned_ip_groups",
    "detect_orphaned_private_dns_zones",
    "detect_orphaned_private_endpoints",
    "detect_empty_resource_groups",
    "detect_failed_api_connections",
    "detect_expired_certificates",
    # Convenience list
    "ALL_DETECTORS",
]
