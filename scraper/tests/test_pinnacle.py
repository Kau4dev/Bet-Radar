"""
tests/test_pinnacle.py
-----------------------
Testes unitários para extractors/pinnacle.py (The Odds API).

Usa `respx` para mockar chamadas HTTP do httpx sem fazer requests reais.
A variável ODDS_API_KEY é injetada via monkeypatch.

Casos testados (7):
1. Partida encontrada — retorna odds de múltiplos bookmakers
2. Partida não encontrada em nenhuma liga
3. Chave de API inválida (HTTP 401) — retorna [] e para sem retry
4. Liga sem eventos (HTTP 422) — pula para próxima liga
5. Resposta malformada — outcomes sem "Draw"
6. Separadores variados na query (vs, X, versus)
7. Rate limit (HTTP 429) — retorna [] sem lançar exceção
"""

import os
import pytest
import respx
import httpx

from extractors.pinnacle import PinnacleExtractor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def extractor():
    return PinnacleExtractor()


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    """Injeta uma chave fake para todos os testes."""
    monkeypatch.setenv("ODDS_API_KEY", "test-key-fake-12345")


def _odds_url(sport_key: str) -> str:
    return f"{PinnacleExtractor.BASE_URL}/sports/{sport_key}/odds/"


def _make_event(home: str, away: str, bk_key: str, bk_title: str,
                home_price: float, draw_price: float, away_price: float) -> dict:
    """Cria um evento no formato retornado pela The Odds API."""
    return {
        "id": "abc123",
        "sport_key": "soccer_brazil_campeonato",
        "home_team": home,
        "away_team": away,
        "commence_time": "2026-04-24T20:00:00Z",
        "bookmakers": [
            {
                "key": bk_key,
                "title": bk_title,
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": home,   "price": home_price},
                            {"name": away,   "price": away_price},
                            {"name": "Draw", "price": draw_price},
                        ]
                    }
                ]
            }
        ]
    }


# Primeira liga da lista que o extractor itera
_FIRST_SPORT = PinnacleExtractor.SOCCER_SPORT_KEYS[0]


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_match_found_single_bookmaker(extractor):
    """Caso 1a: Partida encontrada com um bookmaker."""
    respx.get(_odds_url(_FIRST_SPORT)).mock(
        return_value=httpx.Response(200, json=[
            _make_event("Flamengo", "Vasco da Gama", "bet365", "Bet365",
                        1.95, 3.40, 4.10)
        ], headers={"x-requests-remaining": "499", "x-requests-used": "1"})
    )

    result = await extractor.extract("Flamengo x Vasco")

    assert len(result) == 1
    odd = result[0]
    assert odd["bookmaker"] == "Bet365"
    assert odd["team_home"] == "Flamengo"
    assert odd["team_away"] == "Vasco da Gama"
    assert odd["odds"]["home_win"] == 1.95
    assert odd["odds"]["draw"] == 3.40
    assert odd["odds"]["away_win"] == 4.10
    assert odd["match_id"] == "flamengo_v_vasco_da_gama"
    assert "timestamp" in odd


@pytest.mark.asyncio
@respx.mock
async def test_match_found_multiple_bookmakers(extractor):
    """Caso 1b: Mesmo evento com dois bookmakers — deve retornar 2 odds."""
    event = {
        "id": "xyz999",
        "sport_key": _FIRST_SPORT,
        "home_team": "Palmeiras",
        "away_team": "Corinthians",
        "commence_time": "2026-04-24T21:00:00Z",
        "bookmakers": [
            {
                "key": "bet365", "title": "Bet365",
                "markets": [{"key": "h2h", "outcomes": [
                    {"name": "Palmeiras",   "price": 2.10},
                    {"name": "Corinthians", "price": 3.50},
                    {"name": "Draw",        "price": 3.20},
                ]}]
            },
            {
                "key": "pinnacle", "title": "Pinnacle",
                "markets": [{"key": "h2h", "outcomes": [
                    {"name": "Palmeiras",   "price": 2.15},
                    {"name": "Corinthians", "price": 3.45},
                    {"name": "Draw",        "price": 3.25},
                ]}]
            },
        ]
    }

    respx.get(_odds_url(_FIRST_SPORT)).mock(
        return_value=httpx.Response(200, json=[event],
                                    headers={"x-requests-remaining": "498", "x-requests-used": "2"})
    )

    result = await extractor.extract("Palmeiras x Corinthians")

    assert len(result) == 2
    bookmakers_found = {r["bookmaker"] for r in result}
    assert "Bet365" in bookmakers_found
    assert "Pinnacle" in bookmakers_found


@pytest.mark.asyncio
@respx.mock
async def test_match_not_found(extractor):
    """Caso 2: Partida não encontrada em nenhuma liga (todas retornam eventos diferentes)."""
    # Mocka todas as ligas para retornar uma partida diferente da buscada
    for sport_key in PinnacleExtractor.SOCCER_SPORT_KEYS:
        respx.get(_odds_url(sport_key)).mock(
            return_value=httpx.Response(200, json=[
                _make_event("Juventus", "Inter Milan", "bet365", "Bet365", 2.30, 3.20, 3.10)
            ], headers={"x-requests-remaining": "490", "x-requests-used": "10"})
        )

    result = await extractor.extract("Flamengo x Vasco")
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_invalid_api_key(extractor, monkeypatch):
    """Caso 3: Chave de API inválida (HTTP 401) — deve retornar [] imediatamente."""
    respx.get(_odds_url(_FIRST_SPORT)).mock(
        return_value=httpx.Response(401, json={"message": "Invalid API key"})
    )

    result = await extractor.extract("Real Madrid x Barcelona")

    assert result == []
    # Deve ter feito apenas 1 request (para de tentar ao receber 401)
    assert respx.calls.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_league_unavailable_422(extractor):
    """Caso 4: Liga sem eventos (HTTP 422) — deve pular e tentar próxima liga."""
    # Primeira liga retorna 422 (indisponível)
    respx.get(_odds_url(_FIRST_SPORT)).mock(
        return_value=httpx.Response(422, json={"message": "Sport not found"})
    )
    # Segunda liga retorna a partida
    second_sport = PinnacleExtractor.SOCCER_SPORT_KEYS[1]
    respx.get(_odds_url(second_sport)).mock(
        return_value=httpx.Response(200, json=[
            _make_event("Flamengo", "Vasco", "bet365", "Bet365", 1.90, 3.50, 4.20)
        ], headers={"x-requests-remaining": "497", "x-requests-used": "3"})
    )

    result = await extractor.extract("Flamengo x Vasco")
    assert len(result) == 1
    assert result[0]["bookmaker"] == "Bet365"


@pytest.mark.asyncio
@respx.mock
async def test_malformed_response_no_draw(extractor):
    """Caso 5: Outcomes sem 'Draw' — mercado h2h sem empate (eliminatória)."""
    event_no_draw = {
        "id": "elim001",
        "home_team": "Brasil",
        "away_team": "Argentina",
        "bookmakers": [
            {
                "key": "bet365", "title": "Bet365",
                "markets": [{"key": "h2h", "outcomes": [
                    {"name": "Brasil",    "price": 2.10},
                    {"name": "Argentina", "price": 1.75},
                    # Sem "Draw" — eliminatória
                ]}]
            }
        ]
    }

    respx.get(_odds_url(_FIRST_SPORT)).mock(
        return_value=httpx.Response(200, json=[event_no_draw],
                                    headers={"x-requests-remaining": "496", "x-requests-used": "4"})
    )

    # Para mercados sem empate, a partida não é incluída (odds 1X2 incompletas)
    result = await extractor.extract("Brasil x Argentina")
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_various_query_separators(extractor):
    """Caso 6: Separadores variados na query — 'vs', 'X', 'versus'."""
    respx.get(_odds_url(_FIRST_SPORT)).mock(
        return_value=httpx.Response(200, json=[
            _make_event("Bayern Munich", "Dortmund", "pinnacle", "Pinnacle",
                        1.80, 4.00, 4.50)
        ], headers={"x-requests-remaining": "495", "x-requests-used": "5"})
    )

    for separator in [" vs ", " X ", " versus "]:
        # Reseta o respx entre chamadas
        respx.get(_odds_url(_FIRST_SPORT)).mock(
            return_value=httpx.Response(200, json=[
                _make_event("Bayern Munich", "Dortmund", "pinnacle", "Pinnacle",
                            1.80, 4.00, 4.50)
            ], headers={"x-requests-remaining": "494", "x-requests-used": "6"})
        )
        result = await extractor.extract(f"Bayern Munich{separator}Dortmund")
        assert len(result) >= 1, f"Falhou com separador '{separator}'"


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_429(extractor):
    """Caso 7: Rate limit (HTTP 429) — deve retornar [] sem lançar exceção."""
    for sport_key in PinnacleExtractor.SOCCER_SPORT_KEYS:
        respx.get(_odds_url(sport_key)).mock(
            return_value=httpx.Response(429, json={"message": "Too Many Requests"})
        )

    result = await extractor.extract("Flamengo x Vasco")
    assert result == []


@pytest.mark.asyncio
async def test_missing_api_key_returns_empty(extractor, monkeypatch):
    """Caso extra: ODDS_API_KEY não definida — retorna [] com log de erro."""
    monkeypatch.delenv("ODDS_API_KEY", raising=False)

    result = await extractor.extract("Flamengo x Vasco")
    assert result == []
