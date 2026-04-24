"""
extractors/pinnacle.py
-----------------------
Extractor para Pinnacle via API REST pública (sem necessidade de Playwright).

A Pinnacle expõe uma API JSON acessível com uma X-API-Key pública conhecida.
Esta é a implementação mais rápida e confiável — prioridade 1 de implementação.

Fluxo:
    1. Busca todas as ligas de futebol (/sports/29/leagues)
    2. Para cada liga (top 50 por popularidade), busca os matchups
    3. Compara os nomes dos times com a query usando fuzzy match
    4. Se encontrar, extrai as odds 1X2 e retorna no schema RawOddDTO
"""

import logging

import httpx

from extractors.base_extractor import BaseExtractor
from utils.match_id import build_match_id, parse_match_query
from utils.normalizer import match_is_target
from utils.retry import async_retry

logger = logging.getLogger(__name__)


class PinnacleExtractor(BaseExtractor):
    """
    Extractor de odds da Pinnacle usando a API REST arcadia (não oficial, mas pública).

    A API não requer autenticação real — a X-API-Key é pública e amplamente conhecida.
    Retorna JSON estruturado, sem necessidade de parsear HTML ou executar JavaScript.
    """

    BOOKMAKER_NAME = "Pinnacle"

    # Base URL da API arcadia (usada pelo frontend da Pinnacle)
    BASE_URL = "https://pinnacle.bet.br/sportsbook"

    # ID do esporte futebol na API da Pinnacle
    SOCCER_SPORT_ID = 29

    # Headers necessários para simular o browser client
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "X-API-Key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R",
        "Referer": "https://www.pinnacle.com/",
        "Accept": "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }

    # Número máximo de ligas a verificar (ligas são ordenadas por popularidade)
    MAX_LEAGUES_TO_CHECK = 50

    async def extract(self, match_query: str) -> list[dict]:
        """
        Busca odds para a partida informada na Pinnacle.

        Args:
            match_query: Ex: "Real Madrid x Barcelona"

        Returns:
            Lista com 0 ou 1 dict no schema RawOddDTO.
        """
        try:
            query_home, query_away = parse_match_query(match_query)
        except ValueError as exc:
            logger.warning(f"[Pinnacle] Query inválida: {exc}")
            return []

        logger.info(f"[Pinnacle] Buscando: {query_home} x {query_away}")

        try:
            async with httpx.AsyncClient(
                headers=self.HEADERS,
                timeout=httpx.Timeout(15.0, connect=10.0),
                follow_redirects=True,
            ) as client:
                leagues = await self._fetch_leagues(client)
                if not leagues:
                    logger.warning("[Pinnacle] Nenhuma liga retornada pela API.")
                    return []

                # Itera pelas ligas mais populares
                for league in leagues[: self.MAX_LEAGUES_TO_CHECK]:
                    league_id = league.get("id")
                    if not league_id:
                        continue

                    odd = await self._find_match_in_league(
                        client, league_id, query_home, query_away
                    )
                    if odd:
                        logger.info(
                            f"[Pinnacle] ✅ Partida encontrada na liga '{league.get('name', league_id)}'"
                        )
                        return [odd]

        except httpx.HTTPError as exc:
            logger.error(f"[Pinnacle] Erro HTTP: {exc}")
        except Exception as exc:
            logger.error(f"[Pinnacle] Erro inesperado: {exc}")

        logger.info(f"[Pinnacle] Partida não encontrada: {match_query}")
        return []

    @async_retry(max_attempts=3, base_delay=1.0, exceptions=(httpx.HTTPError,))
    async def _fetch_leagues(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Busca todas as ligas de futebol ordenadas por popularidade.

        Endpoint: GET /sports/{sport_id}/leagues?brandId=0
        """
        resp = await client.get(
            f"{self.BASE_URL}/sports/{self.SOCCER_SPORT_ID}/leagues",
            params={"brandId": "0", "jurisdiction": "0"},
        )
        resp.raise_for_status()
        return resp.json()

    @async_retry(max_attempts=2, base_delay=0.5, exceptions=(httpx.HTTPError,))
    async def _find_match_in_league(
        self,
        client: httpx.AsyncClient,
        league_id: int,
        query_home: str,
        query_away: str,
    ) -> dict | None:
        """
        Busca matchups de uma liga específica e verifica se a partida alvo está presente.

        Endpoint: GET /leagues/{league_id}/matchups
        Retorna list de matchups com participants e prices.
        """
        try:
            resp = await client.get(f"{self.BASE_URL}/leagues/{league_id}/matchups")
            if resp.status_code != 200:
                return None

            matchups = resp.json()
            if not isinstance(matchups, list):
                return None

            for matchup in matchups:
                # Apenas eventos ao vivo ou futuros (type: "matchup", não "special")
                if matchup.get("type") != "matchup":
                    continue

                participants = matchup.get("participants", [])
                if len(participants) < 2:
                    continue

                # Pinnacle: participante[0] = home, participante[1] = away
                home_name = participants[0].get("name", "")
                away_name = participants[1].get("name", "")

                if not match_is_target(home_name, away_name, query_home, query_away):
                    continue

                # Encontrou a partida — extrai as odds 1X2
                return self._parse_odds(matchup, home_name, away_name)

        except Exception as exc:
            logger.debug(f"[Pinnacle] Erro ao processar liga {league_id}: {exc}")
            return None

        return None

    def _parse_odds(self, matchup: dict, home_name: str, away_name: str) -> dict | None:
        """
        Extrai as odds 1X2 do matchup retornado pela API da Pinnacle.

        Estrutura esperada em matchup["prices"]:
            [{"designation": "home", "price": 2.40}, ...]
        """
        prices = matchup.get("prices", [])
        if not prices:
            logger.debug(f"[Pinnacle] Matchup sem prices: {matchup.get('id')}")
            return None

        try:
            home_price = next(
                p["price"] for p in prices if p.get("designation") == "home"
            )
            draw_price = next(
                p["price"] for p in prices if p.get("designation") == "draw"
            )
            away_price = next(
                p["price"] for p in prices if p.get("designation") == "away"
            )

            return self.build_odd_payload(
                bookmaker=self.BOOKMAKER_NAME,
                match_id=build_match_id(home_name, away_name),
                team_home=home_name,
                team_away=away_name,
                home_win=float(home_price),
                draw=float(draw_price),
                away_win=float(away_price),
            )

        except StopIteration:
            logger.debug(
                f"[Pinnacle] Odds 1X2 incompletas para: {home_name} x {away_name}. "
                "Pode ser mercado sem empate (ex: eliminatória)."
            )
            return None
        except (KeyError, ValueError) as exc:
            logger.warning(f"[Pinnacle] Erro ao parsear prices: {exc}")
            return None
