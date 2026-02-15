"""Azure Portal deep link generation."""

import webbrowser


def get_portal_url(resource_id: str, tenant_id: str) -> str:
    """Generate Azure Portal URL for a resource.

    Args:
        resource_id: Full Azure resource ID
        tenant_id: Azure tenant ID (GUID)

    Returns:
        URL to open resource in Azure Portal
    """
    return f"https://portal.azure.com/#@{tenant_id}/resource{resource_id}"


def open_in_portal(resource_id: str, tenant_id: str) -> None:
    """Open resource in Azure Portal using default browser.

    Args:
        resource_id: Full Azure resource ID
        tenant_id: Azure tenant ID (GUID)
    """
    url = get_portal_url(resource_id, tenant_id)
    webbrowser.open(url)
