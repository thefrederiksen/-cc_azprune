# cc_azprune - Implementation Handover

**For**: Implementing Agent
**Date**: 2026-02-15
**PRD**: See `docs/PRD.md` for full requirements

---

## What to Build

A Python desktop application that scans Azure subscriptions for orphaned resources and displays them in a sortable grid.

## Tech Stack (Decided)

| Component | Choice |
|-----------|--------|
| Language | Python 3.11+ |
| UI | CustomTkinter |
| Azure | azure-identity, azure-mgmt-resourcegraph |
| Excel | openpyxl |
| Packaging | PyInstaller |

## Project Structure

```
cc_azprune/
  src/
    cc_azprune/
      __init__.py
      app.py              # Main window with CustomTkinter
      scanner.py          # Azure Resource Graph queries
      detectors/
        __init__.py
        nic.py            # Orphaned NICs
        disk.py           # Unattached disks
        public_ip.py      # Unused public IPs
      grid.py             # Grid/table component
      exporter.py         # Excel export
      portal_links.py     # Azure Portal URL builder
      costs.py            # Cost estimation
  tests/
  pyproject.toml
  README.md
  LICENSE                 # MIT
```

## Implementation Order

### Step 1: Project Setup
1. Create `pyproject.toml` with dependencies
2. Set up src layout
3. Create basic CustomTkinter window that launches

### Step 2: Azure Authentication
1. Check for existing `az login` session using DefaultAzureCredential
2. Display subscription name in UI header
3. Show clear error if not authenticated

### Step 3: Resource Graph Scanner
1. Implement scanner.py with Resource Graph client
2. Create detector for orphaned NICs first (simplest)
3. Return list of resource dictionaries

### Step 4: Grid Display
1. Create CTkScrollableFrame with table layout
2. Column headers: Name, Type, Resource Group, Location, Cost
3. Add sorting on header click
4. Add search box that filters rows

### Step 5: Additional Detectors
1. Add unattached disk detection
2. Add unused public IP detection
3. Add cost estimates (hardcoded for MVP)

### Step 6: Portal Links
1. Add "Open" button per row
2. Open browser to: `https://portal.azure.com/#@{tenantId}/resource{resourceId}`

### Step 7: Excel Export
1. Add "Export to Excel" button
2. Save all visible rows to .xlsx
3. Default filename: `azure-orphans-YYYY-MM-DD.xlsx`

### Step 8: Polish
1. Progress indicator during scan
2. Total count and estimated savings at bottom
3. Error handling for network/auth issues
4. README with screenshots

## Key Azure Queries

**Orphaned NICs**:
```kusto
Resources
| where type == 'microsoft.network/networkinterfaces'
| where isnull(properties.virtualMachine)
| project name, resourceGroup, location, id, subscriptionId
```

**Unattached Disks**:
```kusto
Resources
| where type == 'microsoft.compute/disks'
| where isnull(properties.managedBy)
| where properties.diskState != 'ActiveSAS'
| project name, resourceGroup, location, id, properties.diskSizeGB
```

**Unused Public IPs**:
```kusto
Resources
| where type == 'microsoft.network/publicipaddresses'
| where isnull(properties.ipConfiguration)
| project name, resourceGroup, location, id
```

## Cost Estimates (Hardcoded for MVP)

| Resource | Monthly Cost |
|----------|--------------|
| NIC | $0 (note if has Public IP) |
| Public IP (Basic) | $3.65 |
| Public IP (Standard) | $4.00 |
| Disk | ~$0.05/GB (Standard HDD) |

## Portal URL Format

```python
def get_portal_url(resource_id: str, tenant_id: str) -> str:
    return f"https://portal.azure.com/#@{tenant_id}/resource{resource_id}"
```

## Testing Strategy

1. Manual testing against mindzie Azure subscription
2. Known orphaned resource: `mindziedev927` (NIC) in development resource group
3. Unit tests for URL generation and cost calculation

## Success Criteria

- [ ] App launches with CustomTkinter UI
- [ ] Click "Scan" and see orphaned resources
- [ ] Sort by any column
- [ ] Search filters results
- [ ] Click "Open" goes to Azure Portal
- [ ] Export saves valid Excel file

## Out of Scope (v1.0)

- Delete functionality
- Multi-subscription support
- NSG, App Service Plan, Snapshot detection (v1.1)
- Dark mode

---

**Start with Step 1.** Read PRD.md for full context if needed.
