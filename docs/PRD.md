# cc_azprune - Product Requirements Document

**Version**: 0.2
**Author**: Soren Frederiksen
**Company**: Center Consulting Inc.
**Date**: 2026-02-15
**Status**: Draft
**Repository**: https://github.com/CenterConsultingInc/cc_azprune (to be created)

---

## 1. Executive Summary

**cc_azprune** is an open-source desktop application that identifies orphaned and unused Azure resources. It displays results in a searchable grid with cost estimates and direct links to Azure Portal for remediation.

### The Problem

Azure subscriptions accumulate orphaned resources:
- VMs deleted but NICs and public IPs left behind
- Disks detached but never removed
- App Service Plans with no apps

Azure's cost tools bury this in convoluted dashboards. No simple "show me what's wasting money" view exists.

### The Solution

A desktop app with one button: **Scan**. Results appear in a grid you can sort, search, and export to Excel. Click any resource to open it directly in Azure Portal.

---

## 2. Goals and Non-Goals

### Goals
- Single-button scan of Azure subscription
- Grid view with sort and search
- Show estimated cost per resource
- Direct links to Azure Portal
- Export to Excel
- Cross-platform (Windows, Mac, Linux)

### Non-Goals (v1)
- Delete functionality (navigate to Portal instead)
- Multi-subscription scan (single subscription first)
- CI/CD integration (this is a desktop app)
- Web-based version

---

## 3. User Stories

### US-1: Quick Scan
> As a DevOps engineer, I want to click one button and see all orphaned resources so I can decide what to clean up.

**Acceptance Criteria**:
- Click "Scan" button
- See progress indicator
- Grid populates with orphaned resources
- Can sort by any column

### US-2: Find Expensive Resources
> As a FinOps analyst, I want to sort by cost so I can prioritize cleanup.

**Acceptance Criteria**:
- Cost column shows estimated monthly cost
- Can sort descending to see most expensive first
- Costs are clearly labeled (per month)

### US-3: Navigate to Portal
> As a developer, I want to click a resource and go directly to it in Azure Portal so I can delete it.

**Acceptance Criteria**:
- Each row has "Open in Portal" link/button
- Clicking opens browser to exact resource
- No authentication required (uses existing browser session)

### US-4: Export for Reporting
> As an IT manager, I want to export the list to Excel so I can share with my team.

**Acceptance Criteria**:
- "Export" button saves .xlsx file
- All columns included
- File opens in Excel correctly

---

## 4. Functional Requirements

### 4.1 Authentication

| ID | Requirement |
|----|-------------|
| FR-AUTH-01 | Use existing Azure CLI session (`az login`) |
| FR-AUTH-02 | Show clear error if not logged in |
| FR-AUTH-03 | Display subscription name in UI |

### 4.2 Scanning

| ID | Requirement |
|----|-------------|
| FR-SCAN-01 | Single "Scan" button triggers scan |
| FR-SCAN-02 | Progress indicator during scan |
| FR-SCAN-03 | Scan completes in < 10 seconds for typical subscription |
| FR-SCAN-04 | Show count of orphaned resources found |

### 4.3 Resource Detection

| Resource Type | Detection Logic | Cost Estimate |
|--------------|-----------------|---------------|
| Network Interface | `virtualMachine == null` | $0 (note: may hold Public IP) |
| Managed Disk | `managedBy == null` AND `diskState != 'ActiveSAS'` | Based on size/tier |
| Public IP | `ipConfiguration == null` | ~$3.65/mo (Basic), ~$4/mo (Standard) |
| App Service Plan | No web apps deployed | Based on tier |
| Network Security Group | Not attached to NIC or subnet | $0 (clutter) |
| Snapshot | Source disk deleted OR age > 90 days | ~$0.05/GB/mo |

### 4.4 Grid Display

| ID | Requirement |
|----|-------------|
| FR-GRID-01 | Show columns: Name, Type, Resource Group, Location, Cost, Actions |
| FR-GRID-02 | Sort by any column (click header) |
| FR-GRID-03 | Search/filter box filters all columns |
| FR-GRID-04 | Show total estimated cost at bottom |

### 4.5 Azure Portal Links

| ID | Requirement |
|----|-------------|
| FR-LINK-01 | Each row has "Open in Portal" action |
| FR-LINK-02 | Link opens default browser |
| FR-LINK-03 | Link goes directly to resource blade |

**URL Pattern**:
```
https://portal.azure.com/#@{tenantId}/resource{resourceId}
```

Example:
```
https://portal.azure.com/#@456981be-9ca7-43b0-8b7c-7b88e5927af5/resource/subscriptions/e8e96b94-f972-427f-8ce5-8017f08e9cf6/resourceGroups/development/providers/Microsoft.Network/networkInterfaces/mindziedev927
```

### 4.6 Excel Export

| ID | Requirement |
|----|-------------|
| FR-EXPORT-01 | "Export to Excel" button |
| FR-EXPORT-02 | Saves .xlsx file with all data |
| FR-EXPORT-03 | Include columns: Name, Type, Resource Group, Location, Cost, Portal URL |
| FR-EXPORT-04 | Default filename: `azure-orphans-YYYY-MM-DD.xlsx` |

---

## 5. UI Wireframe

```
+------------------------------------------------------------------+
|  cc_azprune - Azure Orphaned Resource Finder                     |
+------------------------------------------------------------------+
|  Subscription: mindzie studio - Development                      |
|                                                                   |
|  [Scan]                              Search: [____________]       |
|                                                                   |
+------------------------------------------------------------------+
|  Name            | Type      | Resource Group | Location | Cost  |
+------------------------------------------------------------------+
|  mindziedev927   | NIC       | development    | eastus2  | $0*   |
|  mindziedev-ip   | Public IP | development    | eastus2  | $3.65 |
|  old-snapshot-1  | Snapshot  | backups        | eastus   | $2.50 |
+------------------------------------------------------------------+
|  * NIC is free but holds Public IP costing $3.65/mo              |
|                                                                   |
|  Total Orphaned Resources: 3                                      |
|  Estimated Monthly Savings: $6.15                                 |
|                                                                   |
|  [Export to Excel]                                                |
+------------------------------------------------------------------+
```

---

## 6. Technical Architecture

### 6.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Azure SDK maturity |
| UI Framework | CustomTkinter | Modern look, cross-platform |
| Azure SDK | azure-identity, azure-mgmt-resourcegraph | Official SDKs |
| Excel Export | openpyxl | Standard library for .xlsx |
| Packaging | PyInstaller | Single executable |

### 6.2 Project Structure

```
cc_azprune/
  src/
    cc_azprune/
      __init__.py
      app.py              # Main application window
      scanner.py          # Azure Resource Graph queries
      detectors/
        nic.py
        disk.py
        public_ip.py
        nsg.py
        app_service_plan.py
        snapshot.py
      grid.py             # Grid/table component
      exporter.py         # Excel export
      portal_links.py     # Azure Portal URL generation
      costs.py            # Cost estimation
  tests/
  pyproject.toml
  README.md
  LICENSE
```

### 6.3 Azure Portal Deep Link Format

```python
def get_portal_url(resource_id: str, tenant_id: str) -> str:
    return f"https://portal.azure.com/#@{tenant_id}/resource{resource_id}"
```

### 6.4 Resource Graph Queries

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
| project name, resourceGroup, location, id, properties.diskSizeGB, subscriptionId
```

---

## 7. MVP Scope (v1.0)

### In Scope
- [x] Scan button
- [x] Detect: NICs, Disks, Public IPs (3 resource types)
- [x] Grid with sorting
- [x] Search/filter
- [x] Cost estimates
- [x] Azure Portal links
- [x] Excel export

### Out of Scope (v1.1+)
- [ ] Additional resource types (NSG, App Service Plan, Snapshot, etc.)
- [ ] Multi-subscription support
- [ ] Subscription picker dropdown
- [ ] Refresh/rescan button
- [ ] Dark mode

---

## 8. Success Metrics

| Metric | Target |
|--------|--------|
| GitHub Stars (6 months) | 50+ |
| Personal use | Saving money on mindzie Azure subscription |
| Portfolio value | Demonstrates Python + Azure + UI skills |

---

## 9. Implementation Phases

### Phase 1: Core Scan (Week 1)
- [ ] Set up Python project with CustomTkinter
- [ ] Implement Azure authentication check
- [ ] Create Resource Graph scanner for NICs
- [ ] Display results in basic grid

### Phase 2: Full Detection (Week 2)
- [ ] Add disk detection
- [ ] Add public IP detection
- [ ] Add cost estimation logic
- [ ] Improve grid (sorting, column widths)

### Phase 3: Polish (Week 3)
- [ ] Add search/filter
- [ ] Add Azure Portal links
- [ ] Add Excel export
- [ ] Error handling and edge cases
- [ ] README and documentation

### Phase 4: Release
- [ ] Create GitHub repository
- [ ] PyInstaller executable for Windows
- [ ] GitHub release with downloadable exe
- [ ] Announce on LinkedIn

---

## 10. Open Questions

1. **UI Framework**: CustomTkinter vs PyQt vs Electron?
   - CustomTkinter: Simple, looks good, pure Python
   - PyQt: More powerful, licensing complexity
   - Electron: Web tech, larger bundle size

2. **Cost data source**: Hardcode estimates or query Azure Pricing API?
   - Recommendation: Hardcode for MVP, pricing API for v1.1

3. **Distribution**: PyPI package or standalone exe?
   - Recommendation: Both - pip install for devs, exe for non-devs

---

## Appendix A: Real Orphaned Resource Found

**Subscription**: mindzie studio - Development (2026-02-15)

| Resource | Type | Problem | Est. Cost |
|----------|------|---------|-----------|
| mindziedev927 | NIC | Not attached to any VM | $0 |
| mindziedev-ip | Public IP | Attached to orphaned NIC | ~$3.65/mo |

---

*Document Version History*

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-02-15 | Soren Frederiksen | Initial draft (CLI version) |
| 0.2 | 2026-02-15 | Soren Frederiksen | Changed to desktop app, added grid UI, Portal links, Excel export |
