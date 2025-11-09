from functools import lru_cache
from typing import Optional

import requests


PRIVATE_IP_PREFIXES = (
    "127.",
    "10.",
    "192.168.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "169.254.",
    "::1",
    "fc",
    "fd",
)


@lru_cache(maxsize=1024)
def resolve_ip_location(ip_address: Optional[str]) -> Optional[dict]:
    """
    Resolve a rough location for an IP address using ipapi.co.

    Returns a dictionary containing country, region, city and coordinates
    when available. Private or invalid addresses return None.
    """
    if not ip_address:
        return None

    normalized = ip_address.strip()
    if any(normalized.startswith(prefix) for prefix in PRIVATE_IP_PREFIXES):
        return None

    try:
        response = requests.get(
            f"https://ipapi.co/{normalized}/json/",
            timeout=2.5,
        )
        if response.status_code != 200:
            return None

        payload = response.json()
        if payload.get("error"):
            return None

        return {
            "country": payload.get("country_name"),
            "region": payload.get("region"),
            "city": payload.get("city"),
            "postal": payload.get("postal"),
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
        }
    except requests.RequestException:
        return None


