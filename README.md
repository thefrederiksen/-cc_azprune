# cc_azprune

Azure Orphaned Resource Finder - A desktop app to identify unused Azure resources.

## Features

- Single-button scan of Azure subscription
- Detects orphaned NICs, unattached disks, and unused public IPs
- Grid view with sorting and search
- Shows estimated monthly cost per resource
- Direct links to Azure Portal for cleanup
- Export to Excel

## Installation

```bash
pip install cc_azprune
```

Or for development:

```bash
git clone https://github.com/CenterConsultingInc/cc_azprune.git
cd cc_azprune
pip install -e .
```

## Usage

1. Ensure you're logged into Azure CLI: `az login`
2. Run the app: `cc_azprune`
3. Click "Scan" to find orphaned resources
4. Click "Open" on any resource to view it in Azure Portal
5. Export to Excel for reporting

## Requirements

- Python 3.11+
- Azure CLI with active login session

## License

MIT
