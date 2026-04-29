"""
tests/test_superbet.py
-----------------------
Testes unitários para extractors/superbet.py.

Usa unittest.mock para simular o Playwright sem abrir navegador real.
Cobre tanto respostas REST quanto GraphQL (Superbet usa ambos).

Casos testados (8):
 1. Partida encontrada via API REST simples -> odds corretas
 2. Partida encontrada via wrapper GraphQL -> odds corretas
 3. Partida nao encontrada -> retorna []
 4. Resposta com content-type nao-JSON -> ignorada
 5. Resposta com status != 200 -> ignorada
 6. Evento com mercado por fallback (3 selecoes sem nome) -> extraido
 7. Query invalida -> retorna [] sem abrir browser
 8. _search_events: estrutura aninhada GraphQL
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from extractors.superbet import SuperbetExtractor


@pytest.fixture
def extractor():
    return SuperbetExtractor()


def _make_rest_event(home, away, hw=1.9, dr=3.4, aw=4.1):
    return {
        "homeTeamName": home,
        "awayTeamName": away,
        "markets": [
            {
                "name": "1X2",
                "selections": [
                    {"decimalOdds": hw},
                    {"decimalOdds": dr},
                    {"decimalOdds": aw},
                ]
            }
        ]
    }


def _make_browser_context(api_data=None, status=200, content_type="application/json"):
    mock_response = AsyncMock()
    mock_response.url = "https://superbet.bet.br/graphql"
    mock_response.status = status
    mock_response.headers = {"content-type": content_type}
    mock_response.json = AsyncMock(return_value=api_data or {})

    mock_page = AsyncMock()
    mock_page.on = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.locator = MagicMock(return_value=AsyncMock(
        is_visible=AsyncMock(return_value=False)
    ))

    mock_ctx = AsyncMock()
    mock_ctx.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_ctx)
    mock_browser.close = AsyncMock()

    mock_pw = AsyncMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

    return mock_pw, mock_page, mock_response


async def _fire_response_handler(mock_page, mock_response):
    calls = [c for c in mock_page.on.call_args_list if c.args[0] == "response"]
    if calls:
        handler = calls[-1].args[1]
        await handler(mock_response)


@pytest.mark.asyncio
async def test_match_found_via_rest(extractor, monkeypatch):
    """Caso 1: Partida encontrada via API REST."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    api_data = {"events": [_make_rest_event("Flamengo", "Vasco da Gama", hw=2.1, dr=3.3, aw=3.9)]}
    mock_pw, mock_page, mock_response = _make_browser_context(api_data=api_data)

    with patch("extractors.superbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*a, **kw):
            await _fire_response_handler(mock_page, mock_response)
        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert len(result) == 1
    odd = result[0]
    assert odd["bookmaker"] == "Superbet"
    assert odd["team_home"] == "Flamengo"
    assert odd["team_away"] == "Vasco da Gama"
    assert odd["odds"]["home_win"] == pytest.approx(2.1, rel=1e-3)
    assert odd["odds"]["draw"] == pytest.approx(3.3, rel=1e-3)
    assert odd["odds"]["away_win"] == pytest.approx(3.9, rel=1e-3)
    assert "match_id" in odd and "timestamp" in odd


@pytest.mark.asyncio
async def test_match_found_via_graphql(extractor, monkeypatch):
    """Caso 2: Partida encontrada via wrapper GraphQL."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    api_data = {
        "data": {
            "GetEventsByFilter": {
                "events": [_make_rest_event("Palmeiras", "Corinthians", hw=2.2, dr=3.1, aw=3.4)]
            }
        }
    }
    mock_pw, mock_page, mock_response = _make_browser_context(api_data=api_data)

    with patch("extractors.superbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*a, **kw):
            await _fire_response_handler(mock_page, mock_response)
        mock_page.goto = fake_goto

        result = await extractor.extract("Palmeiras x Corinthians")

    assert len(result) == 1
    assert result[0]["team_home"] == "Palmeiras"
    assert result[0]["odds"]["home_win"] == pytest.approx(2.2, rel=1e-3)


@pytest.mark.asyncio
async def test_match_not_found(extractor, monkeypatch):
    """Caso 3: API retorna outro jogo."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    api_data = {"events": [_make_rest_event("Juventus", "Inter Milan")]}
    mock_pw, mock_page, mock_response = _make_browser_context(api_data=api_data)

    with patch("extractors.superbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*a, **kw):
            await _fire_response_handler(mock_page, mock_response)
        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
async def test_non_json_content_type_ignored(extractor, monkeypatch):
    """Caso 4: Content-type nao-JSON e descartado silenciosamente."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    mock_pw, mock_page, mock_response = _make_browser_context(
        api_data={}, content_type="text/plain"
    )

    with patch("extractors.superbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*a, **kw):
            await _fire_response_handler(mock_page, mock_response)
        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
async def test_non_200_status_ignored(extractor, monkeypatch):
    """Caso 5: Status 403 ignorado, retorna []."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    mock_pw, mock_page, mock_response = _make_browser_context(status=403)

    with patch("extractors.superbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*a, **kw):
            await _fire_response_handler(mock_page, mock_response)
        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
async def test_market_fallback_3_selections(extractor, monkeypatch):
    """Caso 6: Mercado sem nome mas com 3 selecoes e extraido por fallback."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    event = {
        "homeTeamName": "Sao Paulo",
        "awayTeamName": "Santos",
        "markets": [{"selections": [{"price": 2.0}, {"price": 3.2}, {"price": 3.8}]}]
    }
    mock_pw, mock_page, mock_response = _make_browser_context(api_data={"events": [event]})

    with patch("extractors.superbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*a, **kw):
            await _fire_response_handler(mock_page, mock_response)
        mock_page.goto = fake_goto

        result = await extractor.extract("Sao Paulo x Santos")

    assert len(result) == 1
    assert result[0]["odds"]["draw"] == pytest.approx(3.2, rel=1e-3)


@pytest.mark.asyncio
async def test_invalid_query_returns_empty(extractor):
    """Caso 7: Query sem separador reconhecido."""
    result = await extractor.extract("FlamengoPenteado")
    assert result == []


def test_search_events_graphql_nested(extractor):
    """Caso 8: _search_events com estrutura GraphQL aninhada."""
    graphql_data = {
        "data": {
            "GetEventsByFilter": {
                "events": [_make_rest_event("Atletico Mineiro", "Cruzeiro", hw=1.95, dr=3.6, aw=4.0)]
            }
        }
    }
    result = extractor._search_events(graphql_data, "Atletico", "Cruzeiro")
    assert len(result) == 1
    assert result[0]["team_home"] == "Atletico Mineiro"
    assert result[0]["odds"]["home_win"] == pytest.approx(1.95, rel=1e-3)
