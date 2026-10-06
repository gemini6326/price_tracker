"""Sitios de Mercado Libre soportados; cada catálogo conserva su moneda y país."""

SITES = {
    "MCO": {
        "country": "Colombia",
        "currency": "COP",
        "host": "www.mercadolibre.com.co",
        "auth": "https://auth.mercadolibre.com.co/authorization",
    },
    "MLC": {
        "country": "Chile",
        "currency": "CLP",
        "host": "www.mercadolibre.cl",
        "auth": "https://auth.mercadolibre.cl/authorization",
    },
}

HOST_SITES = {
    host: site_id
    for site_id, site in SITES.items()
    for host in (site["host"], site["host"].removeprefix("www."))
}


def site_for_id(external_id: str) -> dict[str, str]:
    return SITES[external_id[:3].upper()]
