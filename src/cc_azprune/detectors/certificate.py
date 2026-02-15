"""Detector for expired App Service Certificates."""

from datetime import datetime
from typing import Any

from ..costs import estimate_certificate_cost, format_cost
from ..resource_info import get_risk_level


QUERY = """
Resources
| where type == "microsoft.web/certificates"
| extend expirationDate = todatetime(properties.expirationDate)
| where expirationDate < now()
| project id, name, resourceGroup, location, subscriptionId,
          expirationDate,
          issuer = properties.issuer,
          subjectName = properties.subjectName,
          thumbprint = properties.thumbprint
"""


def detect_expired_certificates(query_func) -> list[dict[str, Any]]:
    """Detect expired App Service Certificates.

    Expired certificates represent a security/operational risk,
    not necessarily a cost (they're one-time purchases).

    Args:
        query_func: Function to execute Resource Graph query

    Returns:
        List of expired Certificate resources
    """
    results = query_func(QUERY)

    resources = []
    for item in results:
        name = item.get("name", "")
        exp_date = item.get("expirationDate", "")
        issuer = item.get("issuer", "")
        subject = item.get("subjectName", "")
        thumbprint = item.get("thumbprint", "")

        cost = estimate_certificate_cost()

        # Calculate days expired
        days_expired = ""
        if exp_date:
            try:
                exp = datetime.fromisoformat(str(exp_date).replace("Z", "+00:00"))
                now = datetime.now(exp.tzinfo)
                delta = now - exp
                days_expired = f"Expired {delta.days} days ago"
            except Exception:
                pass

        # Build details
        details_parts = []

        if days_expired:
            details_parts.append(days_expired)

        if subject and len(subject) < 40:
            details_parts.append(f"Subject: {subject}")

        if issuer and len(issuer) < 30:
            details_parts.append(f"Issuer: {issuer}")

        if thumbprint:
            details_parts.append(f"Thumb: {thumbprint[:8]}...")

        resources.append({
            "name": name,
            "type": "microsoft.web/certificates",
            "type_display": "Certificate",
            "resource_group": item.get("resourceGroup", ""),
            "location": item.get("location", ""),
            "id": item.get("id", ""),
            "subscription_id": item.get("subscriptionId", ""),
            "cost": cost,
            "cost_display": format_cost(cost),
            "details": " | ".join(details_parts) if details_parts else "Expired certificate",
            "risk_level": get_risk_level("microsoft.web/certificates"),
        })

    return resources
