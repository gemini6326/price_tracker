"""Colombia: no mezclar países ni multiplicar por 100 los precios mostrados."""

import json
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from tracker import meli
from tracker.config import settings
from tracker.processors.mercadolibre import MercadoLibreProcessor, _catalog_of

ml = MercadoLibreProcessor()
URL = "https://www.mercadolibre.com.co/p/MCO67417938"


@pytest.mark.parametrize("url", [URL, URL.replace("www.", ""), URL + "?modo=nacional"])
def test_enlaces_colombia(url):
    assert ml.matches(url)
    ref = ml.normalize(url)
    assert ref.external_id == "MCO67417938"
    assert ref.canonical_url.startswith(URL)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.mercadolibre.cl/p/MCO67417938",
        "https://www.mercadolibre.com.co/p/MLC48419682",
        URL + "invalid",
        "https://mercadolibre.com.co.evil.com/p/MCO67417938",
    ],
)
def test_rechaza_pais_incorrecto_y_enlaces_invalidos(url):
    assert not ml.matches(url)
    with pytest.raises(ValueError):
        ml.normalize(url)


def offers():
    return json.dumps(
        {
            "product": {
                "name": "Consola Colombia",
                "pictures": [{"url": "https://example.com/a.jpg"}],
            },
            "items": [
                {
                    "item_id": "MCO1",
                    "currency_id": "COP",
                    "price": 1999900,
                    "original_price": 2499900,
                    "official_store_id": 1,
                },
                {"item_id": "MCO2", "currency_id": "COP", "price": 1800000},
                {"item_id": "MCO3", "currency_id": "COP", "price": 1500000, "tags": ["cbt_item"]},
                {"item_id": "MLC1", "currency_id": "CLP", "price": 1},
            ],
        }
    )


def test_cop_unidad_minima_y_modos():
    result = ml.parse(offers(), ml.normalize(URL))
    assert (result.price, result.list_price, result.currency, result.available) == (
        199990000,
        249990000,
        "COP",
        True,
    )
    assert ml.parse(offers(), ml.normalize(URL + "?modo=nacional")).price == 180000000
    assert ml.parse(offers(), ml.normalize(URL + "?modo=todos")).price == 150000000
    variants = ml.parse_variants(offers(), ml.normalize(URL))
    assert len(variants) == 3
    assert "COP $1.999.900" in variants[0].label
    assert all(v.url.startswith(URL) for v in variants)


def test_agotado_colombia_conserva_moneda():
    result = ml.parse('{"product": {"name": "Consola"}, "items": []}', ml.normalize(URL))
    assert result.currency == "COP" and result.price is None and not result.available


async def test_publicacion_busca_en_colombia(monkeypatch):
    _catalog_of.clear()
    calls = []

    async def get(path, params=None):
        calls.append((path, params))
        body = (
            {"results": [{"id": "MLC99"}, {"id": "MCO67417938"}]}
            if params
            else {
                "results": [{"user_product_id": "MCOU123", "price": 1999900, "currency_id": "COP"}]
            }
        )
        return httpx.Response(200, json=body)

    monkeypatch.setattr(meli, "get", get)
    ref = ml.normalize("https://www.mercadolibre.com.co/consola-colombia/up/MCOU123")
    assert await ml._catalog_for(ref) == "MCO67417938"
    assert calls[0][1]["site_id"] == "MCO"
    assert all("MLC99" not in path for path, _ in calls)
    raw = json.loads(offers())
    raw["items"][0]["user_product_id"] = "MCOU123"
    assert ml.parse(json.dumps(raw), ref).price == 199990000
    assert ml.parse_variants(json.dumps(raw), ref) == []


def test_oauth_colombia_con_pkce(monkeypatch):
    monkeypatch.setattr(settings, "meli_site_id", "MCO")
    monkeypatch.setattr(settings, "meli_client_id", "test-client")
    url = urlparse(meli.authorization_url())
    query = parse_qs(url.query)
    assert url.netloc == "auth.mercadolibre.com.co"
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == [settings.meli_redirect_uri]
    assert query["state"][0] in meli._pending
