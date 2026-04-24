"""
extractors/superbet.py
-----------------------
Extractor para Superbet Brasil via Playwright + intercepção de rede.
Segue o mesmo padrão do BetanoExtractor.

URL alvo: https://superbet.com.br/apostas-esportivas/futebol

A Superbet usa uma SPA React/Next.js com API GraphQL ou REST interna.
API interna identificada via DevTools > Network:
    POST /graphql  (payload: operationName: "GetEventsByFilter")
    GET  /api/v1/events?sportId=1&...
    GET  /api/sports/soccer/events

⚠️ Superbet usa GraphQL — o payload POST é JSON com query e variables.
⚠️ Seletores CSS são gerados por CSS Modules — muito frágeis.
"""

import logging
import random

from playwright.async_api import async_playwright, Response, TimeoutError as PWTimeout

from extractors.base_extractor import BaseExtractor
from utils.match_id import build_match_id, parse_match_query
from utils.normalizer import match_is_target

logger = logging.getLogger(__name__)


class SuperbetExtractor(BaseExtractor):
    BOOKMAKER_NAME = "Superbet"
    SOCCER_URL = "https://superbet.com/pt-br/apostas-esportivas/futebol"

    # Padrões da API/GraphQL da Superbet
    API_PATTERNS = [
        "/graphql",
        "/api/v1/events",
        "/api/sports/",
        "superbet.com.br/api/",
        "/api/offer/",
    ]

    # ⚠️ FRÁGIL: seletores gerados por CSS Modules (hash no nome da classe)
    SEL_EVENT = "[data-testid='event-row'], [class*='EventRow'], [class*='event-item']"
    SEL_ODDS = "[data-testid='odd-value'], [class*='OddValue'], [class*='odd-value']"

    async def extract(self, match_query: str) -> list[dict]:
        try:
            query_home, query_away = parse_match_query(match_query)
        except ValueError as exc:
            logger.warning(f"[Superbet] Query inválida: {exc}")
            return []

        logger.info(f"[Superbet] Buscando: {query_home} x {query_away}")
        collected: list[dict] = []

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage",
                          "--disable-blink-features=AutomationControlled"],
                )
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="pt-BR",
                    timezone_id="America/Sao_Paulo",
                    viewport={"width": 1440, "height": 900},
                )
                page = await ctx.new_page()

                async def handle_response(response: Response) -> None:
                    if not any(p in response.url for p in self.API_PATTERNS):
                        return
                    if response.status != 200:
                        return
                    try:
                        ct = response.headers.get("content-type", "")
                        if "json" not in ct:
                            return
                        data = await response.json()
                        collected.extend(self._search_events(data, query_home, query_away))
                    except Exception as e:
                        logger.debug(f"[Superbet] Erro ao parsear resposta: {e}")

                page.on("response", handle_response)
                await page.goto(self.SOCCER_URL, wait_until="networkidle", timeout=35_000)
                await page.wait_for_timeout(random.randint(3_000, 5_000))

                if not collected:
                    collected.extend(await self._fallback_dom(page, query_home, query_away))

                await browser.close()

        except PWTimeout:
            logger.error("[Superbet] Timeout ao carregar a página.")
        except Exception as e:
            logger.error(f"[Superbet] Erro inesperado: {e}")

        logger.info(f"[Superbet] Odds coletadas: {len(collected)}")
        return collected

    def _search_events(self, data, query_home: str, query_away: str) -> list[dict]:
        """
        Suporta respostas REST e GraphQL da Superbet.
        GraphQL: {"data": {"events": [...]}} ou {"data": {"GetEventsByFilter": {"events": [...]}}}
        REST: {"events": [...]} ou lista direta
        """
        events = []

        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            # GraphQL wrapper
            gql_data = data.get("data", {})
            if isinstance(gql_data, dict):
                for key, val in gql_data.items():
                    if isinstance(val, list):
                        events.extend(val)
                    elif isinstance(val, dict):
                        events.extend(val.get("events", []))
            # REST direto
            for key in ["events", "fixtures", "results", "data"]:
                val = data.get(key, [])
                if isinstance(val, list):
                    events.extend(val)

        results = []
        for event in events:
            try:
                home = (event.get("homeTeamName") or event.get("homeName")
                        or event.get("home", {}).get("name", "")
                        or event.get("homeTeam", {}).get("name", "")
                        or event.get("team1", ""))
                away = (event.get("awayTeamName") or event.get("awayName")
                        or event.get("away", {}).get("name", "")
                        or event.get("awayTeam", {}).get("name", "")
                        or event.get("team2", ""))

                if not home or not away:
                    continue
                if not match_is_target(home, away, query_home, query_away):
                    continue

                odd = self._parse_markets(event, home, away)
                if odd:
                    results.append(odd)
            except Exception as e:
                logger.debug(f"[Superbet] Erro ao processar evento: {e}")

        return results

    def _parse_markets(self, event: dict, home: str, away: str) -> dict | None:
        """
        Extrai odds 1X2 do evento da Superbet.
        Suporta mercados com nomes em pt-BR, en-US e formato GraphQL.
        """
        markets = (event.get("markets", []) or event.get("odds", [])
                   or event.get("bets", []) or event.get("market", []))

        if isinstance(markets, dict):
            markets = [markets]

        market_names = {
            "1X2", "1x2", "Match Result", "Full Time Result",
            "Resultado Final", "Resultado do Jogo", "Full Time"
        }

        target = None
        for m in markets:
            name = m.get("name", "") or m.get("marketName", "") or m.get("typeName", "")
            if name in market_names:
                target = m
                break
        if not target:
            for m in markets:
                sels = (m.get("selections", []) or m.get("outcomes", [])
                        or m.get("odds", []) or m.get("bets", []))
                if len(sels) == 3:
                    target = m
                    break

        if not target:
            return None

        sels = (target.get("selections", []) or target.get("outcomes", [])
                or target.get("odds", []) or target.get("bets", []))
        try:
            vals = []
            for s in sels:
                price = (s.get("price") or s.get("odd") or s.get("odds")
                         or s.get("value") or s.get("decimalOdds"))
                if price is not None:
                    vals.append(float(price))

            if len(vals) == 3:
                return self.build_odd_payload(
                    bookmaker=self.BOOKMAKER_NAME,
                    match_id=build_match_id(home, away),
                    team_home=home, team_away=away,
                    home_win=vals[0], draw=vals[1], away_win=vals[2],
                )
        except (ValueError, TypeError) as e:
            logger.debug(f"[Superbet] Erro ao converter odds: {e}")

        return None

    async def _fallback_dom(self, page, query_home: str, query_away: str) -> list[dict]:
        """Fallback DOM — muito frágil na Superbet por usar CSS Modules com hash."""
        results = []
        try:
            await page.wait_for_selector(self.SEL_EVENT, timeout=5_000)
            for row in await page.locator(self.SEL_EVENT).all():
                lines = [l.strip() for l in (await row.inner_text()).split("\n") if l.strip()]
                if len(lines) < 2:
                    continue
                home, away = lines[0], lines[1]
                if not match_is_target(home, away, query_home, query_away):
                    continue
                try:
                    odds_els = await row.locator(self.SEL_ODDS).all()
                    if len(odds_els) >= 3:
                        hw = float((await odds_els[0].inner_text()).strip())
                        dr = float((await odds_els[1].inner_text()).strip())
                        aw = float((await odds_els[2].inner_text()).strip())
                        results.append(self.build_odd_payload(
                            bookmaker=self.BOOKMAKER_NAME,
                            match_id=build_match_id(home, away),
                            team_home=home, team_away=away,
                            home_win=hw, draw=dr, away_win=aw,
                        ))
                        break
                except Exception as e:
                    logger.debug(f"[Superbet][DOM] {e}")
        except Exception as e:
            logger.debug(f"[Superbet][DOM] Falha: {e}")
        return results
