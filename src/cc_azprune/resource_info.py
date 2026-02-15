"""Resource information and safety guidance for Azure resource types.

This module provides detailed descriptions, risk levels, and deletion guidance
for each resource type detected by cc_azprune.
"""

# Risk level constants
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"


# Resource type information indexed by Azure resource type string
RESOURCE_INFO = {
    # =========================================================================
    # LOW RISK - Safe to delete, no data loss, easily recreated
    # =========================================================================
    "microsoft.network/networkinterfaces": {
        "friendly_name": "Network Interface (NIC)",
        "risk_level": RISK_LOW,
        "description": "A virtual network adapter that connects a VM to a network.",
        "why_orphaned": "Not attached to any VM. Usually left behind when a VM was deleted.",
        "safe_to_delete": "Yes - NICs don't contain data, just configuration.",
        "check_before_delete": "Verify no VM is being provisioned that needs this NIC.",
        "deletion_impact": "No impact - the NIC is not being used.",
        "recovery_info": "Cannot be recovered, but easily recreated if needed.",
    },
    "microsoft.network/publicipaddresses": {
        "friendly_name": "Public IP Address",
        "risk_level": RISK_LOW,
        "description": "A public IP address that can be assigned to Azure resources.",
        "why_orphaned": "Not attached to any resource (NIC, Load Balancer, etc.).",
        "safe_to_delete": "Yes - Just an IP address, easily recreated.",
        "check_before_delete": "If static IP, verify the IP address isn't documented elsewhere (DNS, firewall rules).",
        "deletion_impact": "You will lose this specific IP address. Dynamic IPs get a new address on recreation.",
        "recovery_info": "Cannot recover the same IP - you'll get a new one.",
    },
    "microsoft.network/networksecuritygroups": {
        "friendly_name": "Network Security Group (NSG)",
        "risk_level": RISK_LOW,
        "description": "A firewall that filters network traffic to/from Azure resources.",
        "why_orphaned": "Not attached to any subnet or network interface.",
        "safe_to_delete": "Yes - Not protecting anything currently.",
        "check_before_delete": "Review the rules - you may want to save them for reference.",
        "deletion_impact": "No impact - the NSG is not filtering any traffic.",
        "recovery_info": "Cannot be recovered, but rules can be recreated.",
    },
    "microsoft.network/routetables": {
        "friendly_name": "Route Table",
        "risk_level": RISK_LOW,
        "description": "Custom routing rules for network traffic in a virtual network.",
        "why_orphaned": "Not attached to any subnet.",
        "safe_to_delete": "Yes - Not routing any traffic currently.",
        "check_before_delete": "Review the routes - you may want to document them.",
        "deletion_impact": "No impact - the route table is not in use.",
        "recovery_info": "Cannot be recovered, but routes can be recreated.",
    },
    "microsoft.compute/availabilitysets": {
        "friendly_name": "Availability Set",
        "risk_level": RISK_LOW,
        "description": "A logical grouping of VMs for high availability (fault/update domains).",
        "why_orphaned": "No VMs are assigned to this availability set.",
        "safe_to_delete": "Yes - Just metadata, no resources inside.",
        "check_before_delete": "Verify no VMs are being provisioned that need this set.",
        "deletion_impact": "No impact - just removes empty container.",
        "recovery_info": "Cannot be recovered, but easily recreated.",
    },
    "microsoft.network/ipgroups": {
        "friendly_name": "IP Group",
        "risk_level": RISK_LOW,
        "description": "A container for IP addresses used in Azure Firewall rules.",
        "why_orphaned": "Not associated with any Azure Firewall or policy.",
        "safe_to_delete": "Yes - Just a list of IPs, not used anywhere.",
        "check_before_delete": "Verify no firewall rules are being created that need this group.",
        "deletion_impact": "No impact - the IP list is not referenced.",
        "recovery_info": "Cannot be recovered, but IP list can be recreated.",
    },
    "microsoft.resources/subscriptions/resourcegroups": {
        "friendly_name": "Resource Group",
        "risk_level": RISK_LOW,
        "description": "A container that holds related Azure resources.",
        "why_orphaned": "Contains no resources.",
        "safe_to_delete": "Yes - Empty container with no resources.",
        "check_before_delete": "Double-check it's truly empty and not reserved for future use.",
        "deletion_impact": "No impact - just removes empty container.",
        "recovery_info": "Cannot be recovered, but easily recreated.",
    },
    "microsoft.network/trafficmanagerprofiles": {
        "friendly_name": "Traffic Manager Profile",
        "risk_level": RISK_LOW,
        "description": "DNS-based traffic load balancer for distributing traffic globally.",
        "why_orphaned": "Has no endpoints configured.",
        "safe_to_delete": "Yes - Not routing any traffic.",
        "check_before_delete": "Verify no DNS records point to this profile.",
        "deletion_impact": "No impact - no endpoints to receive traffic.",
        "recovery_info": "Cannot be recovered, but easily recreated.",
    },
    "microsoft.network/frontdoorwebapplicationfirewallpolicies": {
        "friendly_name": "Front Door WAF Policy",
        "risk_level": RISK_LOW,
        "description": "Web Application Firewall policy for Azure Front Door.",
        "why_orphaned": "Not linked to any Front Door endpoints.",
        "safe_to_delete": "Yes - Not protecting any endpoints.",
        "check_before_delete": "Document custom rules if you want to reuse them later.",
        "deletion_impact": "No impact - policy is not applied anywhere.",
        "recovery_info": "Cannot be recovered, but rules can be recreated.",
    },
    "microsoft.web/connections": {
        "friendly_name": "API Connection",
        "risk_level": RISK_LOW,
        "description": "A connector used by Logic Apps to connect to external services.",
        "why_orphaned": "In Error or Disconnected state - connection is broken.",
        "safe_to_delete": "Yes - Already broken, needs to be fixed or replaced.",
        "check_before_delete": "Check if any Logic Apps reference this connection.",
        "deletion_impact": "Logic Apps using this connection may fail (they may already be failing).",
        "recovery_info": "Create a new connection with the same settings.",
    },
    "microsoft.web/certificates": {
        "friendly_name": "App Service Certificate",
        "risk_level": RISK_LOW,
        "description": "SSL/TLS certificate for securing App Service applications.",
        "why_orphaned": "Certificate has expired.",
        "safe_to_delete": "Yes - Expired certificates provide no security value.",
        "check_before_delete": "Ensure a new certificate has been provisioned.",
        "deletion_impact": "No impact if already replaced. Apps using expired cert are already insecure.",
        "recovery_info": "Purchase or provision a new certificate.",
    },
    "microsoft.network/loadbalancers": {
        "friendly_name": "Load Balancer",
        "risk_level": RISK_LOW,
        "description": "Distributes network traffic across multiple backend resources.",
        "why_orphaned": "Backend pool is empty - no resources to load balance.",
        "safe_to_delete": "Yes - Not routing traffic to any backends.",
        "check_before_delete": "Verify no resources are being added to this load balancer.",
        "deletion_impact": "No impact - no backends receiving traffic.",
        "recovery_info": "Cannot be recovered, but easily recreated.",
    },
    "microsoft.web/serverfarms": {
        "friendly_name": "App Service Plan",
        "risk_level": RISK_LOW,
        "description": "The compute resources (VMs) that host App Service applications.",
        "why_orphaned": "No apps are hosted on this plan.",
        "safe_to_delete": "Yes - Empty plan just costs money with no benefit.",
        "check_before_delete": "Verify no apps are being deployed to this plan.",
        "deletion_impact": "No impact - no apps hosted.",
        "recovery_info": "Cannot be recovered, but easily recreated.",
    },
    "microsoft.sql/servers/elasticpools": {
        "friendly_name": "SQL Elastic Pool",
        "risk_level": RISK_LOW,
        "description": "Shared compute resources for multiple Azure SQL databases.",
        "why_orphaned": "No databases are in this pool.",
        "safe_to_delete": "Yes - Empty pool just costs money with no benefit.",
        "check_before_delete": "Verify no databases are being added to this pool.",
        "deletion_impact": "No impact - no databases in pool.",
        "recovery_info": "Cannot be recovered, but easily recreated.",
    },

    # =========================================================================
    # MEDIUM RISK - Verify before deleting, may contain data or affect services
    # =========================================================================
    "microsoft.compute/disks": {
        "friendly_name": "Managed Disk",
        "risk_level": RISK_MEDIUM,
        "description": "A virtual hard drive that stores VM data (OS or data disk).",
        "why_orphaned": "Not attached to any VM. The original VM may have been deleted.",
        "safe_to_delete": "CAUTION - This disk may contain important data!",
        "check_before_delete": (
            "1. Check disk name for hints about original VM\n"
            "2. Consider mounting to a VM to check contents\n"
            "3. Take a snapshot before deleting if unsure\n"
            "4. Verify data is backed up elsewhere"
        ),
        "deletion_impact": "ALL DATA ON THE DISK WILL BE PERMANENTLY LOST.",
        "recovery_info": "CANNOT be recovered after deletion. Create snapshot first if unsure.",
    },
    "microsoft.compute/virtualmachines": {
        "friendly_name": "Virtual Machine",
        "risk_level": RISK_MEDIUM,
        "description": "A stopped/deallocated VM that is not currently running.",
        "why_orphaned": "VM is deallocated (stopped). May be intentionally stopped.",
        "safe_to_delete": "CAUTION - Verify this VM is not needed before deleting.",
        "check_before_delete": (
            "1. Check with team/owner if VM is still needed\n"
            "2. Verify any data on the VM is backed up\n"
            "3. Check if VM is stopped temporarily (maintenance window)"
        ),
        "deletion_impact": "VM and its OS disk will be deleted. Data disks may remain orphaned.",
        "recovery_info": "Cannot be recovered. Disks may be retained depending on settings.",
    },
    "microsoft.network/privatednszones": {
        "friendly_name": "Private DNS Zone",
        "risk_level": RISK_MEDIUM,
        "description": "A private DNS zone for name resolution within virtual networks.",
        "why_orphaned": "Not linked to any virtual networks.",
        "safe_to_delete": "CAUTION - DNS records may still be needed by applications.",
        "check_before_delete": (
            "1. Check if any apps reference these DNS names\n"
            "2. Verify records are documented elsewhere\n"
            "3. Check if VNet link is being configured"
        ),
        "deletion_impact": "All DNS records in this zone will be deleted.",
        "recovery_info": "Cannot be recovered. Records must be recreated manually.",
    },
    "microsoft.network/privateendpoints": {
        "friendly_name": "Private Endpoint",
        "risk_level": RISK_MEDIUM,
        "description": "A network interface connecting to an Azure service privately.",
        "why_orphaned": "Connection is in Disconnected or Rejected state.",
        "safe_to_delete": "CAUTION - The target service may still need private connectivity.",
        "check_before_delete": (
            "1. Verify the target service doesn't need this endpoint\n"
            "2. Check if connection needs to be re-approved\n"
            "3. Confirm private DNS records can be cleaned up"
        ),
        "deletion_impact": "Private connectivity to the service will be lost.",
        "recovery_info": "Must create a new private endpoint and get approval.",
    },
    "microsoft.network/applicationgateways": {
        "friendly_name": "Application Gateway",
        "risk_level": RISK_MEDIUM,
        "description": "A Layer 7 load balancer for web traffic with WAF capabilities.",
        "why_orphaned": "Backend pools are empty - no servers to route to.",
        "safe_to_delete": "CAUTION - May be in setup phase or temporarily empty.",
        "check_before_delete": (
            "1. Check if backends are being configured\n"
            "2. Verify SSL certificates aren't needed elsewhere\n"
            "3. Document custom WAF rules if configured"
        ),
        "deletion_impact": "All configuration, rules, and SSL certificates will be lost.",
        "recovery_info": "Cannot be recovered. Complex to recreate - document config first.",
    },
    "microsoft.network/natgateways": {
        "friendly_name": "NAT Gateway",
        "risk_level": RISK_MEDIUM,
        "description": "Provides outbound internet connectivity for resources in a subnet.",
        "why_orphaned": "Not attached to any subnets.",
        "safe_to_delete": "CAUTION - Verify subnet outbound connectivity is handled another way.",
        "check_before_delete": (
            "1. Check if subnet is being configured to use this NAT GW\n"
            "2. Verify resources have alternative outbound connectivity\n"
            "3. Confirm public IPs can be released"
        ),
        "deletion_impact": "Associated public IPs may become orphaned.",
        "recovery_info": "Cannot be recovered, but can recreate with same config.",
    },
    "microsoft.network/ddosprotectionplans": {
        "friendly_name": "DDoS Protection Plan",
        "risk_level": RISK_MEDIUM,
        "description": "Protection against DDoS attacks for virtual networks.",
        "why_orphaned": "No virtual networks are protected by this plan.",
        "safe_to_delete": "Yes - VERY expensive ($2,944/mo) with no VNets protected.",
        "check_before_delete": (
            "1. Verify no VNets are being added to this plan\n"
            "2. Confirm DDoS protection strategy with security team"
        ),
        "deletion_impact": "No impact if no VNets are linked.",
        "recovery_info": "Can recreate, but takes time to provision.",
    },

    # =========================================================================
    # HIGH RISK - Critical infrastructure, verify carefully before any action
    # =========================================================================
    "microsoft.network/virtualnetworkgateways": {
        "friendly_name": "VNet Gateway",
        "risk_level": RISK_HIGH,
        "description": "Gateway for VPN or ExpressRoute connectivity to on-premises.",
        "why_orphaned": "No connections and no VPN clients configured.",
        "safe_to_delete": "HIGH RISK - Verify no VPN/ExpressRoute connectivity is needed.",
        "check_before_delete": (
            "1. Check with network team about connectivity requirements\n"
            "2. Verify no on-premises connections exist\n"
            "3. Confirm no point-to-site VPN users need access\n"
            "4. Check for any BGP peering configurations"
        ),
        "deletion_impact": "ALL VPN/ExpressRoute connectivity will be lost. Very expensive to recreate.",
        "recovery_info": "Provisioning takes 30-45 minutes. All connections must be reconfigured.",
    },
}


def get_resource_info(resource_type: str) -> dict:
    """Get resource information for a given Azure resource type.

    Args:
        resource_type: The Azure resource type string (e.g., 'microsoft.compute/disks')

    Returns:
        Dictionary with resource info, or default values if type not found
    """
    resource_type_lower = resource_type.lower()

    if resource_type_lower in RESOURCE_INFO:
        return RESOURCE_INFO[resource_type_lower]

    # Return default info for unknown types
    return {
        "friendly_name": resource_type.split("/")[-1].title(),
        "risk_level": RISK_MEDIUM,
        "description": "Azure resource.",
        "why_orphaned": "Detected as potentially unused.",
        "safe_to_delete": "Verify before deleting.",
        "check_before_delete": "Review resource details and check with team.",
        "deletion_impact": "Unknown - verify with Azure documentation.",
        "recovery_info": "Varies by resource type.",
    }


def get_risk_level(resource_type: str) -> str:
    """Get just the risk level for a resource type.

    Args:
        resource_type: The Azure resource type string

    Returns:
        Risk level: 'low', 'medium', or 'high'
    """
    info = get_resource_info(resource_type)
    return info.get("risk_level", RISK_MEDIUM)


def get_safety_display(risk_level: str) -> tuple[str, str]:
    """Get display text and color for a risk level.

    Args:
        risk_level: The risk level ('low', 'medium', 'high')

    Returns:
        Tuple of (display_text, color_code)
    """
    if risk_level == RISK_LOW:
        return "[OK]", "#4A7C4E"  # Green
    elif risk_level == RISK_HIGH:
        return "[WARN]", "#C75050"  # Red
    else:  # MEDIUM
        return "[CHECK]", "#B8860B"  # Dark goldenrod/yellow
