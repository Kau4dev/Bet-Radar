"""
extractors/sportingbet.py
--------------------------
Extractor para Sportingbet via Playwright + intercepção de rede.
Segue o mesmo padrão do BetanoExtractor.

API interna: /api/widget/, /api/v2/sports/, /api/offer/events
URL alvo: https://sports.sportingbet.com/pt-br/sports/futebol

⚠️ Seletores CSS são frágeis — verificar periodicamente via DevTools.
"""

import logging
import random

from playwright.async_api import async_playwright, Response, TimeoutError as PWTimeout

from extractors.base_extractor import BaseExtractor
from utils.match_id import build_match_id, parse_match_query
from utils.normalizer import match_is_target

logger = logging.getLogger(__name__)


class SportingbetExtractor(BaseExtractor):
    BOOKMAKER_NAME = "Sportingbet"
    SOCCER_URL = "https://sports.sportingbet.com/pt-br/sports/futebol"

    API_PATTERNS = ["/api/widget/", "/api/v2/sports/", "/api/offer/", "sportingbet.com/api/"]
    SEL_EVENT = "[class*='event-row'], [data-testid='event'], [class*='EventRow']"
    SEL_ODDS = "[class*='odd-button'], [data-testid='odd'], [class*='OddButton']"

    async def extract(self, match_query: str) -> list[dict]:
        try:
            query_home, query_away = parse_match_query(match_query)
        except ValueError as exc:
            logger.warning(f"[Sportingbet] Query inválida: {exc}")
            return []

        logger.info(f"[Sportingbet] Buscando: {query_home} x {query_away}")
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
                    viewport={"width": 1366, "height": 768},
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
                        logger.debug(f"[Sportingbet] Erro ao parsear API: {e}")

                page.on("response", handle_response)
                await page.goto(self.SOCCER_URL, wait_until="networkidle", timeout=30_000)
                await page.wait_for_timeout(random.randint(2_500, 4_000))

                if not collected:
                    collected.extend(await self._fallback_dom(page, query_home, query_away))

                await browser.close()

        except PWTimeout:
            logger.error("[Sportingbet] Timeout ao carregar a página.")
        except Exception as e:
            logger.error(f"[Sportingbet] Erro inesperado: {e}")

        logger.info(f"[Sportingbet] Odds coletadas: {len(collected)}")
        return collected

    def _search_events(self, data, query_home: str, query_away: str) -> list[dict]:
        events = []
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            for key in ["events", "data", "fixtures", "results"]:
                val = data.get(key, [])
                if isinstance(val, list):
                    events.extend(val)

        results = []
        for event in events:
            try:
                home = (event.get("homeName") or event.get("homeTeam")
                        or event.get("home", {}).get("name", "")
                        or event.get("team1", ""))
                away = (event.get("awayName") or event.get("awayTeam")
                        or event.get("away", {}).get("name", "")
                        or event.get("team2", ""))
                if not home or not away:
                    continue
                if not match_is_target(home, away, query_home, query_away):
                    continue
                odd = self._parse_markets(event, home, away)
                if odd:
                    results.append(odd)
            except Exception as e:
                logger.debug(f"[Sportingbet] Erro no evento: {e}")
        return results

    def _parse_markets(self, event: dict, home: str, away: str) -> dict | None:
        markets = event.get("markets", []) or event.get("odds", []) or event.get("bets", [])
        market_names = {"1X2", "1x2", "Match Result", "Full Time Result", "Resultado Final"}

        target = None
        for m in markets:
            if (m.get("name", "") or m.get("marketName", "")) in market_names:
                target = m
                break
        if not target:
            for m in markets:
                sels = m.get("selections", []) or m.get("outcomes", [])
                if len(sels) == 3:
                    target = m
                    break
        if not target:
            return None

        sels = target.get("selections", []) or target.get("outcomes", [])
        try:
            vals = [float(s.get("price") or s.get("odd") or s.get("value") or 0)
                    for s in sels if s.get("price") or s.get("odd") or s.get("value")]
            if len(vals) == 3:
                return self.build_odd_payload(
                    bookmaker=self.BOOKMAKER_NAME,
                    match_id=build_match_id(home, away),
                    team_home=home, team_away=away,
                    home_win=vals[0], draw=vals[1], away_win=vals[2],
                )
        except (ValueError, TypeError) as e:
            logger.debug(f"[Sportingbet] Odds inválidas: {e}")
        return None

    async def _fallback_dom(self, page, query_home: str, query_away: str) -> list[dict]:
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
                    logger.debug(f"[Sportingbet][DOM] {e}")
        except Exception as e:
            logger.debug(f"[Sportingbet][DOM] Falha: {e}")
        return results
