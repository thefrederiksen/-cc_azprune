# Azure Resource Cleanup Guide

This document describes how to identify and remove unused Azure resources to reduce costs.

## Overview

On 2026-02-17, we performed a cleanup across all mindzie Azure subscriptions and saved approximately **$121/month (~$1,450/year)**.

## Azure Advisor

Azure Advisor is a built-in Azure service that analyzes resource usage and provides recommendations.

### Access via Portal
1. Go to https://portal.azure.com
2. Search for "Advisor"
3. Click the "Cost" tab

### Access via CLI

```powershell
# List cost recommendations
az advisor recommendation list --category Cost --output table

# All categories: Cost, Security, Reliability, OperationalExcellence, Performance
az advisor recommendation list --output table
```

## CLI Commands Used

### Prerequisites

```powershell
# Login to Azure
az login

# List all subscriptions
az account list --query "[].{Name:name, Id:id, State:state}" --output table

# Switch subscription
az account set --subscription "<subscription-id>"

# Show current subscription
az account show --output table
```

### Find Unused Public IPs

Public IPs cost ~$4/month each even when not attached to anything.

```powershell
# List unattached public IPs
az network public-ip list --query "[?ipConfiguration==null].{Name:name, IP:ipAddress, ResourceGroup:resourceGroup}" --output table

# Delete an unused public IP
az network public-ip delete --name <ip-name> --resource-group <resource-group>
```

### Find Orphaned Network Interfaces

NICs without attached VMs are usually leftover from deleted VMs.

```powershell
# List orphaned NICs
az network nic list --query "[?virtualMachine==null].{Name:name, ResourceGroup:resourceGroup}" --output table

# Delete an orphaned NIC
az network nic delete --name <nic-name> --resource-group <resource-group>
```

### Find Unattached Disks

Managed disks cost money even when not attached to a VM.

```powershell
# List unattached disks
az disk list --query "[?diskState=='Unattached'].{Name:name, Size:diskSizeGb, SKU:sku.name, ResourceGroup:resourceGroup}" --output table

# Delete an unattached disk
az disk delete --name <disk-name> --resource-group <resource-group> --yes
```

### Find Old Snapshots

```powershell
# List all snapshots
az snapshot list --query "[].{Name:name, Size:diskSizeGb, Created:timeCreated, ResourceGroup:resourceGroup}" --output table

# Delete a snapshot
az snapshot delete --name <snapshot-name> --resource-group <resource-group>
```

### List All Resources

```powershell
# List all resources in current subscription
az resource list --query "[].{Name:name, Type:type, ResourceGroup:resourceGroup}" --output table

# List resources in a specific resource group
az resource list --resource-group <resource-group> --output table
```

### Check VMs

```powershell
# List all VMs with power state
az vm list -d --query "[].{Name:name, PowerState:powerState, Size:hardwareProfile.vmSize, ResourceGroup:resourceGroup}" --output table
```

### Check App Service Plans

```powershell
# List App Service Plans (these have fixed monthly costs)
az appservice plan list --query "[].{Name:name, SKU:sku.name, Tier:sku.tier, Workers:sku.capacity, ResourceGroup:resourceGroup}" --output table
```

### Check SQL Databases

```powershell
# List SQL servers
az sql server list --query "[].{Name:name, ResourceGroup:resourceGroup}" --output table

# List databases on a server
az sql db list --server <server-name> --resource-group <resource-group> --query "[].{Name:name, SKU:currentSku.name, Tier:currentSku.tier, Status:status}" --output table
```

### Check Storage Accounts

```powershell
# List storage accounts
az storage account list --query "[].{Name:name, SKU:sku.name, Kind:kind, ResourceGroup:resourceGroup}" --output table
```

### Delete Entire Resource Group

Use with caution - this deletes everything in the group.

```powershell
# Delete resource group (runs in background)
az group delete --name <resource-group> --yes --no-wait

# Check deletion status
az group show --name <resource-group> --query "{Name:name, State:properties.provisioningState}" --output table

# Check if group still exists
az group exists --name <resource-group>
```

## What We Deleted (2026-02-17)

### mindzie studio - Production

| Resource Type | Name | Resource Group | Est. Savings |
|---------------|------|----------------|--------------|
| Public IP | aadds-vnet-ip | mindzieProduction | ~$4/mo |
| Public IP | mindzieProduction2-ip | mindzieProduction | ~$4/mo |
| Public IP | mindzieProductionIP | mindzieProduction | ~$4/mo |
| Network Interface | mindzieProduction | mindzieProduction | - |
| Network Interface | mindzieproduction169 | mindzieProduction | - |
| Resource Group | aaddsmindzie (Azure AD Domain Services) | - | ~$109/mo |

### mindzie studio - Development

| Resource Type | Name | Resource Group | Est. Savings |
|---------------|------|----------------|--------------|
| Network Interface | mindziestudioinstall271_z1 | mindziestudioinstallresource | - |
| Network Interface | mindziedev927 | development | - |

### Total Savings: ~$121/month (~$1,450/year)

## Subscriptions Reviewed

| Subscription | ID | Resources |
|--------------|-----|-----------|
| mindzie studio - Production | 3d40b040-b743-4655-b562-0383aa7c4cb1 | Active |
| mindzie studio - Development | e8e96b94-f972-427f-8ce5-8017f08e9cf6 | Active |
| Microsoft Azure Sponsorship | bc321ec6-c9c2-47d8-9906-0c5c4f716490 | Empty |
| Microsoft Azure Sponsorship | 2385afe4-8ef5-4920-a1ea-a0ca73a60ebd | Empty |
| Azure DevTest subscription 1 | 0db6ce9a-638b-423b-b859-ab0f5dbc06f6 | Empty |
| Azure subscription 1 | 4b5811c3-06c6-42b7-97bd-2913842816ab | Empty |

## Common Cost Drains to Check

1. **Unused Public IPs** - ~$4/month each
2. **Unattached Managed Disks** - Varies by size/tier
3. **Orphaned NICs** - Free, but clutter
4. **Azure AD Domain Services** - $109+/month
5. **Idle VMs** - Check with Azure Advisor
6. **Overprovisioned VMs** - Right-size based on usage
7. **Old Snapshots** - Can accumulate over time
8. **Unused App Service Plans** - Fixed monthly cost
9. **Empty Recovery Services Vaults** - Usually free but check
10. **Log Analytics with high retention** - Pay per GB ingested

## Tips

- Run `az advisor recommendation list --category Cost` regularly
- Check Azure Cost Management in the portal for spending trends
- Set up budget alerts in Azure to get notified of unexpected spending
- Schedule auto-shutdown for dev/test VMs
- Use consumption/serverless tiers where possible
