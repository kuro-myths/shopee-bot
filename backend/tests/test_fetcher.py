"""Tests for the price fetcher helpers."""
from app.services.fetcher import _parse_price, MetaPriceParser


def test_parse_simple_price():
    assert _parse_price("123456") == 123456.0


def test_parse_formatted_price():
    assert _parse_price("Rp 1.234.567") == 1234567.0


def test_parse_decimal_price():
    assert _parse_price("12.34") == 12.34


def test_parse_rejects_zero():
    assert _parse_price("0") is None


def test_parse_rejects_garbage():
    assert _parse_price("gratis") is None


def test_meta_parser_collects_prices():
    html = (
        '<meta property="og:price:amount" content="99999" />'
        '<meta property="product:price:amount" content="88888" />'
    )
    parser = MetaPriceParser()
    parser.feed(html)
    assert parser.prices == ["99999", "88888"]


def test_meta_parser_ignores_other_meta():
    parser = MetaPriceParser()
    parser.feed('<meta property="og:title" content="Halo" />')
    assert parser.prices == []
