"""
tests/test_pinnacle.py
-----------------------
Testes unitários para extractors/pinnacle.py

Usa `respx` para mockar chamadas HTTP do httpx sem fazer requests reais.

Casos testados (mínimo 5):
1. Partida encontrada com odds 1X2 completas
2. Partida não encontrada em nenhuma liga
3. API retorna erro HTTP 500
4. Resposta malformada (JSON inválido / estrutura inesperada)
5. Separadores variados na query (x, vs, X)
6. Odds incompletas (apenas home/away, sem draw — mercado sem empate)
7. Liga retorna lista vazia de matchups
"""

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


def _make_league(league_id: int, name: str) -> dict:
    return {"id": league_id, "name": name, "sport": 29}


def _make_matchup(home: str, away: str, home_price: float, draw_price: float, away_price: float) -> dict:
    return {
        "type": "matchup",
        "id": 12345,
        "participants": [{"name": home}, {"name": away}],
        "prices": [
            {"designation": "home", "price": home_price},
            {"designation": "draw", "price": draw_price},
            {"designation": "away", "price": away_price},
        ],
    }


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_match_found(extractor):
    """Caso 1: Partida encontrada com odds 1X2 completas."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"
    league_url = f"{PinnacleExtractor.BASE_URL}/leagues/100/matchups"

    respx.get(leagues_url).mock(
        return_value=httpx.Response(200, json=[_make_league(100, "La Liga")])
    )
    respx.get(league_url).mock(
        return_value=httpx.Response(200, json=[
            _make_matchup("Real Madrid", "Barcelona", 2.40, 3.10, 2.90)
        ])
    )

    result = await extractor.extract("Real Madrid x Barcelona")

    assert len(result) == 1
    odd = result[0]
    assert odd["bookmaker"] == "Pinnacle"
    assert odd["team_home"] == "Real Madrid"
    assert odd["team_away"] == "Barcelona"
    assert odd["odds"]["home_win"] == 2.40
    assert odd["odds"]["draw"] == 3.10
    assert odd["odds"]["away_win"] == 2.90
    assert odd["match_id"] == "real_madrid_v_barcelona"
    assert "timestamp" in odd


@pytest.mark.asyncio
@respx.mock
async def test_match_not_found(extractor):
    """Caso 2: Partida não encontrada em nenhuma liga."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"
    league_url = f"{PinnacleExtractor.BASE_URL}/leagues/200/matchups"

    respx.get(leagues_url).mock(
        return_value=httpx.Response(200, json=[_make_league(200, "Brasileirao")])
    )
    respx.get(league_url).mock(
        return_value=httpx.Response(200, json=[
            _make_matchup("Palmeiras", "Corinthians", 2.10, 3.40, 3.20)
        ])
    )

    result = await extractor.extract("Flamengo x Vasco")

    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_api_http_error(extractor):
    """Caso 3: API da Pinnacle retorna erro HTTP 500."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"

    respx.get(leagues_url).mock(
        return_value=httpx.Response(500, json={"error": "Internal Server Error"})
    )

    # Deve retornar [] sem propagar exceção
    result = await extractor.extract("Real Madrid x Barcelona")
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_malformed_response_missing_prices(extractor):
    """Caso 4: Matchup sem campo 'prices' — estrutura inesperada."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"
    league_url = f"{PinnacleExtractor.BASE_URL}/leagues/300/matchups"

    malformed_matchup = {
        "type": "matchup",
        "id": 99999,
        "participants": [{"name": "Real Madrid"}, {"name": "Barcelona"}],
        # 'prices' ausente — estrutura inválida
    }

    respx.get(leagues_url).mock(
        return_value=httpx.Response(200, json=[_make_league(300, "La Liga")])
    )
    respx.get(league_url).mock(
        return_value=httpx.Response(200, json=[malformed_matchup])
    )

    result = await extractor.extract("Real Madrid x Barcelona")
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_malformed_response_not_list(extractor):
    """Caso 4b: Matchups retorna dict em vez de lista."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"
    league_url = f"{PinnacleExtractor.BASE_URL}/leagues/400/matchups"

    respx.get(leagues_url).mock(
        return_value=httpx.Response(200, json=[_make_league(400, "Premier League")])
    )
    respx.get(league_url).mock(
        return_value=httpx.Response(200, json={"error": "not a list"})  # estrutura errada
    )

    result = await extractor.extract("Arsenal x Chelsea")
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_various_query_separators(extractor):
    """Caso 5: Diferentes separadores na query do usuário."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"
    league_url = f"{PinnacleExtractor.BASE_URL}/leagues/500/matchups"

    respx.get(leagues_url).mock(
        return_value=httpx.Response(200, json=[_make_league(500, "Bundesliga")])
    )
    respx.get(league_url).mock(
        return_value=httpx.Response(200, json=[
            _make_matchup("Bayern Munich", "Borussia Dortmund", 1.80, 4.00, 4.50)
        ])
    )

    # Testa separador 'vs' em vez de 'x'
    result = await extractor.extract("Bayern Munich vs Borussia Dortmund")
    assert len(result) == 1
    assert result[0]["team_home"] == "Bayern Munich"


@pytest.mark.asyncio
@respx.mock
async def test_incomplete_odds_no_draw(extractor):
    """Caso 6: Matchup sem odd de empate (eliminatória) — deve retornar []."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"
    league_url = f"{PinnacleExtractor.BASE_URL}/leagues/600/matchups"

    matchup_no_draw = {
        "type": "matchup",
        "id": 77777,
        "participants": [{"name": "Brasil"}, {"name": "Argentina"}],
        "prices": [
            {"designation": "home", "price": 2.10},
            # 'draw' ausente — eliminatória sem empate
            {"designation": "away", "price": 3.20},
        ],
    }

    respx.get(leagues_url).mock(
        return_value=httpx.Response(200, json=[_make_league(600, "Copa do Mundo")])
    )
    respx.get(league_url).mock(
        return_value=httpx.Response(200, json=[matchup_no_draw])
    )

    result = await extractor.extract("Brasil x Argentina")
    assert result == []


@pytest.mark.asyncio
@respx.mock
async def test_empty_league(extractor):
    """Caso 7: Liga retorna lista vazia de matchups."""
    leagues_url = f"{PinnacleExtractor.BASE_URL}/sports/29/leagues"
    league_url = f"{PinnacleExtractor.BASE_URL}/leagues/700/matchups"

    respx.get(leagues_url).mock(
        return_value=httpx.Response(200, json=[_make_league(700, "Empty League")])
    )
    respx.get(league_url).mock(
        return_value=httpx.Response(200, json=[])  # sem eventos
    )

    result = await extractor.extract("Flamengo x Vasco")
    assert result == []
