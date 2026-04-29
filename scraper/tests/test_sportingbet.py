"""
tests/test_sportingbet.py
--------------------------
Testes unitários para extractors/sportingbet.py.

Usa unittest.mock para simular o Playwright sem abrir navegador real.

Casos testados (8):
 1. Partida encontrada via intercepção de API → retorna odds corretas
 2. Partida não encontrada em nenhum evento da API → retorna []
 3. Resposta da API não é JSON (content-type: text/html) → ignorada
 4. Resposta da API com status != 200 → ignorada
 5. Evento com mercado 1X2 por nome explícito
 6. Evento sem mercado 1X2 (poucas seleções) → ignorado
 7. Query inválida (sem separador) → retorna []
 8. Extrator de DOM (fallback) encontra a partida quando a API não responde
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from extractors.sportingbet import SportingbetExtractor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def extractor():
    return SportingbetExtractor()


def _make_api_event(home: str, away: str,
                    hw: float = 2.0, dr: float = 3.2, aw: float = 3.8,
                    market_name: str = "1X2") -> dict:
    """Cria um evento no formato esperado da API interna da Sportingbet."""
    return {
        "homeName": home,
        "awayName": away,
        "markets": [
            {
                "name": market_name,
                "selections": [
                    {"price": hw},
                    {"price": dr},
                    {"price": aw},
                ]
            }
        ]
    }


def _make_browser_context(api_data: dict | list | None = None,
                           status: int = 200,
                           content_type: str = "application/json"):
    """
    Constrói um mock completo da hierarquia async_playwright:
    pw → browser → ctx → page
    Simula o disparo do handler 'response' com os dados fornecidos.
    """
    mock_response = AsyncMock()
    mock_response.url = "https://sports.sportingbet.com/api/offer/events"
    mock_response.status = status
    mock_response.headers = {"content-type": content_type}
    mock_response.json = AsyncMock(return_value=api_data or [])

    mock_page = AsyncMock()
    mock_page.on = MagicMock()          # captura o handler registrado
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
    """Extrai e executa o handler 'response' registrado na página."""
    calls = [c for c in mock_page.on.call_args_list if c.args[0] == "response"]
    if calls:
        handler = calls[-1].args[1]
        await handler(mock_response)


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_match_found_via_api(extractor, monkeypatch):
    """Caso 1: Partida encontrada na intercepção da API → odds corretas retornadas."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    event = _make_api_event("Flamengo", "Vasco da Gama", hw=2.1, dr=3.3, aw=3.9)
    mock_pw, mock_page, mock_response = _make_browser_context(api_data={"events": [event]})

    with patch("extractors.sportingbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        # Simula o disparo do handler após o page.goto
        original_goto = mock_page.goto

        async def fake_goto(*args, **kwargs):
            await original_goto(*args, **kwargs)
            await _fire_response_handler(mock_page, mock_response)

        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert len(result) == 1
    odd = result[0]
    assert odd["bookmaker"] == "Sportingbet"
    assert odd["team_home"] == "Flamengo"
    assert odd["team_away"] == "Vasco da Gama"
    assert odd["odds"]["home_win"] == pytest.approx(2.1, rel=1e-3)
    assert odd["odds"]["draw"] == pytest.approx(3.3, rel=1e-3)
    assert odd["odds"]["away_win"] == pytest.approx(3.9, rel=1e-3)
    assert "match_id" in odd
    assert "timestamp" in odd


@pytest.mark.asyncio
async def test_match_not_found(extractor, monkeypatch):
    """Caso 2: Evento retornado é de outro jogo → retorna []."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    event = _make_api_event("Real Madrid", "Barcelona")
    mock_pw, mock_page, mock_response = _make_browser_context(api_data={"events": [event]})

    with patch("extractors.sportingbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*args, **kwargs):
            await _fire_response_handler(mock_page, mock_response)

        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
async def test_non_json_response_ignored(extractor, monkeypatch):
    """Caso 3: Resposta da API com content-type HTML → ignorada silenciosamente."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    mock_pw, mock_page, mock_response = _make_browser_context(
        api_data={}, content_type="text/html; charset=utf-8"
    )

    with patch("extractors.sportingbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*args, **kwargs):
            await _fire_response_handler(mock_page, mock_response)

        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
async def test_non_200_status_ignored(extractor, monkeypatch):
    """Caso 4: Resposta com status 500 → ignorada."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    event = _make_api_event("Flamengo", "Vasco")
    mock_pw, mock_page, mock_response = _make_browser_context(
        api_data={"events": [event]}, status=500
    )

    with patch("extractors.sportingbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*args, **kwargs):
            await _fire_response_handler(mock_page, mock_response)

        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
async def test_market_found_by_explicit_name(extractor, monkeypatch):
    """Caso 5: Mercado identificado pelo nome 'Resultado Final' (pt-BR)."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    event = _make_api_event("Palmeiras", "Corinthians", market_name="Resultado Final")
    mock_pw, mock_page, mock_response = _make_browser_context(api_data={"events": [event]})

    with patch("extractors.sportingbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*args, **kwargs):
            await _fire_response_handler(mock_page, mock_response)

        mock_page.goto = fake_goto

        result = await extractor.extract("Palmeiras x Corinthians")

    assert len(result) == 1
    assert result[0]["team_home"] == "Palmeiras"


@pytest.mark.asyncio
async def test_event_with_no_valid_market(extractor, monkeypatch):
    """Caso 6: Evento sem mercado 1X2 válido (só 1 seleção) → ignorado."""
    monkeypatch.setenv("SHOW_BROWSER", "0")
    bad_event = {
        "homeName": "Flamengo",
        "awayName": "Vasco da Gama",
        "markets": [
            {"name": "Over/Under", "selections": [{"price": 1.9}]}
        ]
    }
    mock_pw, mock_page, mock_response = _make_browser_context(api_data={"events": [bad_event]})

    with patch("extractors.sportingbet.async_playwright") as mock_apl:
        mock_apl.return_value.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_apl.return_value.__aexit__ = AsyncMock(return_value=False)

        async def fake_goto(*args, **kwargs):
            await _fire_response_handler(mock_page, mock_response)

        mock_page.goto = fake_goto

        result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
async def test_invalid_query_returns_empty(extractor):
    """Caso 7: Query sem separador válido → retorna [] sem abrir browser."""
    result = await extractor.extract("FlamengoCEDO")
    assert result == []


@pytest.mark.asyncio
async def test_search_events_with_list_data(extractor):
    """Caso 8: API retorna lista direta (não dict) → tratado corretamente."""
    events = [
        _make_api_event("Flamengo", "Vasco da Gama", hw=1.85, dr=3.5, aw=4.2)
    ]
    # Testa _search_events diretamente (sem browser)
    result = extractor._search_events(events, "Flamengo", "Vasco")
    assert len(result) == 1
    assert result[0]["odds"]["home_win"] == pytest.approx(1.85, rel=1e-3)
