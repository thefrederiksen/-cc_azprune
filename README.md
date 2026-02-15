# cc_azprune

[![Release](https://img.shields.io/github/v/release/thefrederiksen/cc_azprune)](https://github.com/thefrederiksen/cc_azprune/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Azure Orphaned Resource Finder - A desktop app to identify unused Azure resources.

## Download

Download the latest Windows executable from the [Releases](https://github.com/thefrederiksen/cc_azprune/releases/latest) page.

**Requirements:**
- Windows 10/11 (64-bit)
- Azure CLI installed and logged in (`az login`)

No Python installation required - just download and run!

## Features

- Single-button scan of Azure subscription
- Detects orphaned NICs, unattached disks, and unused public IPs
- Grid view with sorting and search
- Shows estimated monthly cost per resource
- Direct links to Azure Portal for cleanup
- Export to Excel

## Usage

1. Ensure you're logged into Azure CLI: `az login`
2. Run the app (double-click the exe or run `cc_azprune` if installed via pip)
3. Click "Scan" to find orphaned resources
4. Click "Open" on any resource to view it in Azure Portal
5. Export to Excel for reporting

## Installation from Source

For developers who want to run from source or contribute:

```bash
# Clone the repository
git clone https://github.com/thefrederiksen/cc_azprune.git
cd cc_azprune

# Install in development mode
pip install -e .

# Run the app
cc_azprune
```

**Requirements for source installation:**
- Python 3.11+
- Azure CLI with active login session

## Building the Executable

To build the executable locally:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run the build script
python build.py
```

The executable will be created in the `dist/` folder.

## Creating a Release

To create a new release:

1. Update the version in `pyproject.toml`
2. Commit and push changes
3. Create and push a version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. GitHub Actions will automatically build and create the release

## License

MIT
