"""
extractors/pinnacle.py
-----------------------
Extractor que usa The Odds API (https://the-odds-api.com) como fonte de dados.

Motivação para migrar da API direta da Pinnacle:
    - A Pinnacle fechou o acesso público à sua API em julho/2025.
    - A URL interna (arcadia / pinnacle.bet.br) retorna HTTP 500.
    - The Odds API é a alternativa oficial recomendada pelo CONTEXT.md do projeto.
    - Plano gratuito: 500 requests/mês (~16/dia) — suficiente para desenvolvimento.
    - Retorna odds de MÚLTIPLOS bookmakers (Bet365, Betano, Pinnacle, etc.) numa
      única chamada, reduzindo o número de requests necessários.

Configuração:
    - Defina ODDS_API_KEY no arquivo .env (obtenha grátis em https://the-odds-api.com)
    - A chave é lida via variável de ambiente para não ser commitada no código.

Fluxo:
    1. Busca todos os esportes disponíveis para descobrir quais ligas de futebol existem
    2. Para cada liga, busca as odds com market h2h (1X2)
    3. Filtra os eventos pelo nome da partida (fuzzy match)
    4. Retorna odds no schema RawOddDTO para CADA bookmaker encontrado no evento
       (assim um único evento pode publicar múltiplas odds no Kafka)
"""

import logging
import os

import httpx

from extractors.base_extractor import BaseExtractor
from utils.match_id import build_match_id, parse_match_query
from utils.normalizer import match_is_target
from utils.retry import async_retry

logger = logging.getLogger(__name__)


class PinnacleExtractor(BaseExtractor):
    """
    Extractor baseado em The Odds API.

    Apesar do nome histórico 'PinnacleExtractor', esta classe agora usa
    The Odds API como fonte, que inclui odds da Pinnacle entre outros bookmakers.

    Chave de API:
        Obtenha gratuitamente em https://the-odds-api.com
        Configure no .env: ODDS_API_KEY=sua_chave_aqui
    """

    BOOKMAKER_NAME = "Pinnacle"

    BASE_URL = "https://api.the-odds-api.com/v4"

    # Ligas de futebol mais relevantes para o mercado BR + Europa.
    # Lista completa em: GET /v4/sports/?apiKey=KEY
    # Usar lista fixa evita gastar requests da cota apenas para listar ligas.
    SOCCER_SPORT_KEYS = [
        "soccer_brazil_campeonato",          # Brasileirão Série A
        "soccer_brazil_serie_b",             # Brasileirão Série B
        "soccer_south_america_cup",          # Copa Libertadores / Sul-Americana
        "soccer_uefa_champs_league",         # Champions League
        "soccer_uefa_europa_league",         # Europa League
        "soccer_epl",                        # Premier League
        "soccer_spain_la_liga",              # La Liga
        "soccer_italy_serie_a",              # Serie A italiana
        "soccer_germany_bundesliga",         # Bundesliga
        "soccer_france_ligue_one",           # Ligue 1
        "soccer_conmebol_copa_libertadores", # Copa Libertadores
    ]

    # Bookmakers a solicitar (os mais relevantes para o mercado BR)
    # Lista completa: GET /v4/sports/{sport}/odds/?apiKey=KEY&regions=eu,uk
    BOOKMAKERS = "pinnacle,bet365,betano,betfair"

    # Regiões onde os bookmakers estão disponíveis
    REGIONS = "eu,uk,us,au"

    async def extract(self, match_query: str) -> list[dict]:
        """
        Busca odds para a partida informada via The Odds API.

        Retorna uma odd por bookmaker encontrado para a partida.
        Ex: se Pinnacle, Bet365 e Betano tiverem odds, retorna 3 dicts.

        Args:
            match_query: Ex: "Real Madrid x Barcelona"

        Returns:
            Lista de dicts no schema RawOddDTO (uma entrada por bookmaker).
        """
        api_key = os.getenv("ODDS_API_KEY", "").strip()
        if not api_key:
            logger.error(
                "[OddsAPI] ODDS_API_KEY não configurada. "
                "Obtenha uma chave gratuita em https://the-odds-api.com e adicione ao .env"
            )
            return []

        try:
            query_home, query_away = parse_match_query(match_query)
        except ValueError as exc:
            logger.warning(f"[OddsAPI] Query inválida: {exc}")
            return []

        logger.info(f"[OddsAPI] Buscando: {query_home} x {query_away}")

        all_odds: list[dict] = []

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0),
                follow_redirects=True,
            ) as client:
                for sport_key in self.SOCCER_SPORT_KEYS:
                    events = await self._fetch_odds(client, api_key, sport_key)
                    if events is None:
                        # None = erro fatal (ex: chave inválida) — para de tentar
                        break
                    if not events:
                        continue

                    found = self._search_match(events, query_home, query_away)
                    if found:
                        logger.info(
                            f"[OddsAPI] ✅ Partida encontrada em '{sport_key}' "
                            f"({len(found)} bookmaker(s))"
                        )
                        all_odds.extend(found)
                        break  # Encontrou — não precisa verificar outras ligas

        except httpx.HTTPError as exc:
            logger.error(f"[OddsAPI] Erro HTTP: {exc}")
        except Exception as exc:
            logger.error(f"[OddsAPI] Erro inesperado: {exc}")

        if not all_odds:
            logger.info(f"[OddsAPI] Partida não encontrada: {match_query}")

        return all_odds

    @async_retry(max_attempts=3, base_delay=2.0, exceptions=(httpx.TransportError, httpx.TimeoutException))
    async def _fetch_odds(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        sport_key: str,
    ) -> list[dict] | None:
        """
        Busca eventos com odds h2h (1X2) para um esporte/liga específico.

        Endpoint: GET /v4/sports/{sport_key}/odds/
        Parâmetros:
            apiKey:      chave de acesso
            regions:     regiões dos bookmakers (eu, uk, us, au)
            markets:     h2h = moneyline / 1X2
            oddsFormat:  decimal (padrão europeu — compatível com o backend)

        Returns:
            Lista de eventos com odds, ou None em erro fatal (chave inválida, etc.)
        """
        url = f"{self.BASE_URL}/sports/{sport_key}/odds/"
        params = {
            "apiKey": api_key,
            "regions": self.REGIONS,
            "markets": "h2h",
            "oddsFormat": "decimal",
            "bookmakers": self.BOOKMAKERS,
        }

        try:
            resp = await client.get(url, params=params)

            # Log do consumo de cota (The Odds API informa nos headers)
            remaining = resp.headers.get("x-requests-remaining", "?")
            used = resp.headers.get("x-requests-used", "?")
            logger.debug(f"[OddsAPI] Cota: {used} usadas / {remaining} restantes")

            if resp.status_code == 401:
                logger.error("[OddsAPI] ❌ Chave de API inválida (HTTP 401). Verifique ODDS_API_KEY no .env")
                return None  # Erro fatal — para o loop de ligas

            if resp.status_code == 422:
                # Liga não disponível ou sem eventos — normal, não é erro
                logger.debug(f"[OddsAPI] Liga '{sport_key}' sem eventos disponíveis.")
                return []

            if resp.status_code == 429:
                logger.warning("[OddsAPI] Rate limit atingido (HTTP 429). Aguardando...")
                return []

            resp.raise_for_status()
            return resp.json()

        except httpx.HTTPStatusError as exc:
            logger.debug(f"[OddsAPI] HTTP {exc.response.status_code} para '{sport_key}'")
            return []

    def _search_match(
        self,
        events: list[dict],
        query_home: str,
        query_away: str,
    ) -> list[dict]:
        """
        Busca a partida alvo nos eventos retornados pela The Odds API e
        extrai as odds de cada bookmaker encontrado.

        Estrutura de um evento retornado pela API:
        {
            "id": "abc123",
            "sport_key": "soccer_epl",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "commence_time": "2026-04-24T15:00:00Z",
            "bookmakers": [
                {
                    "key": "bet365",
                    "title": "Bet365",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Arsenal",  "price": 2.10},
                                {"name": "Chelsea",  "price": 3.40},
                                {"name": "Draw",     "price": 3.20}
                            ]
                        }
                    ]
                }
            ]
        }
        """
        results = []

        for event in events:
            home = event.get("home_team", "")
            away = event.get("away_team", "")

            if not match_is_target(home, away, query_home, query_away):
                continue

            # Encontrou a partida — extrai odds de cada bookmaker
            bookmakers = event.get("bookmakers", [])
            for bk in bookmakers:
                bk_name = bk.get("title", bk.get("key", "Unknown"))
                markets = bk.get("markets", [])

                h2h_market = next(
                    (m for m in markets if m.get("key") == "h2h"), None
                )
                if not h2h_market:
                    continue

                odd = self._parse_h2h_market(h2h_market, bk_name, home, away)
                if odd:
                    results.append(odd)

        return results

    def _parse_h2h_market(
        self,
        market: dict,
        bookmaker_name: str,
        home: str,
        away: str,
    ) -> dict | None:
        """
        Extrai as odds 1X2 de um mercado h2h retornado pela The Odds API.

        Os outcomes do h2h têm:
            - {"name": "Home Team Name", "price": 2.10}  → vitória mandante
            - {"name": "Away Team Name", "price": 3.40}  → vitória visitante
            - {"name": "Draw",           "price": 3.20}  → empate

        O outcome de empate tem name="Draw" independentemente do idioma.
        Os outcomes de vitória têm o nome do time — identificamos por exclusão.
        """
        outcomes = market.get("outcomes", [])
        if len(outcomes) < 3:
            return None

        try:
            # Empate: name == "Draw" (padrão da The Odds API)
            draw_outcome = next(o for o in outcomes if o.get("name") == "Draw")
            draw_price = float(draw_outcome["price"])

            # Os outros 2 são os times — identificar home/away pelo nome
            team_outcomes = [o for o in outcomes if o.get("name") != "Draw"]
            if len(team_outcomes) != 2:
                return None

            # Identifica qual outcome é o mandante
            home_outcome = next(
                (o for o in team_outcomes if match_is_target(o["name"], home, home, home)),
                team_outcomes[0]  # fallback: primeiro é home
            )
            away_outcome = next(
                (o for o in team_outcomes if o is not home_outcome),
                team_outcomes[1]
            )

            home_price = float(home_outcome["price"])
            away_price = float(away_outcome["price"])

            return self.build_odd_payload(
                bookmaker=bookmaker_name,
                match_id=build_match_id(home, away),
                team_home=home,
                team_away=away,
                home_win=home_price,
                draw=draw_price,
                away_win=away_price,
            )

        except (StopIteration, KeyError, ValueError, TypeError) as exc:
            logger.debug(f"[OddsAPI] Erro ao parsear market h2h ({bookmaker_name}): {exc}")
            return None
