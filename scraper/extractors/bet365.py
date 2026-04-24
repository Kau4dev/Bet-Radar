"""
extractors/bet365.py
---------------------
Extractor para Bet365 via Playwright + Stealth.

A Bet365 é a casa de apostas com a proteção anti-bot mais robusta:
    - Cloudflare bot detection
    - Detecção de WebDriver via navigator.webdriver
    - Fingerprinting de Canvas, WebGL e AudioContext
    - Rate limiting agressivo por IP

Estratégia:
    1. playwright-stealth para mascarar automação
    2. Viewport e User-Agent realistas
    3. Navegação com delays aleatórios humanos
    4. Intercepção de API interna (preferência sobre DOM scraping)
    5. Fallback por seletores CSS (frágeis — documentados abaixo)

⚠️ AVISO IMPORTANTE:
    Bet365 bloqueia IPs de datacenter e algumas redes residenciais.
    Em produção, configure PROXY_URL no .env para usar proxy residencial.
    Seletores CSS abaixo são frágeis (classes ofuscadas) — verificar a cada deploy.
"""

import asyncio
import logging
import os
import random

from playwright.async_api import async_playwright, Response, TimeoutError as PWTimeout

from extractors.base_extractor import BaseExtractor
from utils.match_id import build_match_id, parse_match_query
from utils.normalizer import match_is_target

logger = logging.getLogger(__name__)


class Bet365Extractor(BaseExtractor):
    """
    Extractor de odds da Bet365 usando Playwright com stealth mode.

    Tenta primeiro interceptar a API interna (mais estável).
    Fallback para scraping de DOM com seletores CSS (frágeis).
    """

    BOOKMAKER_NAME = "Bet365"
    BASE_URL = "https://www.bet365.bet.br/"

    # URL de entrada — seção de futebol da Bet365
    SOCCER_URL = "https://www.bet365.com/#/AS/B1/"

    # ⚠️ FRÁGIL: seletores com classes ofuscadas — mudam a cada deploy da Bet365
    # Estratégia: usar atributos mais estáveis quando disponíveis
    SEL_EVENT_TEAMS = "[class*='rcl-ParticipantFixtureDetailsTeam_TeamNames']"
    SEL_ODD_BUTTON = "[class*='gl-ParticipantOddsOnly_Odds'], [class*='gl-Participant_General']"
    SEL_SEARCH_BOX = "[class*='hm-SearchBoxMobile'], [class*='hm-SearchBar'], input[placeholder*='earch']"

    # Padrões da API interna (identificados via DevTools — podem mudar)
    API_PATTERNS = [
        "/api/bet365/",
        "bet365.com/en/api/",
        "/bet/api/",
        "/OC/api/",
    ]

    async def extract(self, match_query: str) -> list[dict]:
        """
        Busca odds para a partida informada na Bet365.

        Args:
            match_query: Ex: "Real Madrid x Barcelona"

        Returns:
            Lista com 0 ou 1 dict no schema RawOddDTO.
        """
        try:
            query_home, query_away = parse_match_query(match_query)
        except ValueError as exc:
            logger.warning(f"[Bet365] Query inválida: {exc}")
            return []

        logger.info(f"[Bet365] Buscando: {query_home} x {query_away}")

        collected_odds: list[dict] = []
        proxy_url = os.getenv("PROXY_URL")

        try:
            async with async_playwright() as pw:
                launch_args = {
                    "headless": True,
                    "args": [
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-extensions",
                        "--disable-plugins",
                        "--disable-infobars",
                        "--window-size=1366,768",
                    ],
                }
                if proxy_url:
                    launch_args["proxy"] = {"server": proxy_url}
                    logger.info(f"[Bet365] Usando proxy: {proxy_url}")

                browser = await pw.chromium.launch(**launch_args)

                ctx_args = {
                    "user_agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "viewport": {"width": 1366, "height": 768},
                    "locale": "pt-BR",
                    "timezone_id": "America/Sao_Paulo",
                    "extra_http_headers": {
                        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                    },
                }
                ctx = await browser.new_context(**ctx_args)

                # Injeta scripts de stealth para mascarar automação
                # playwright-stealth modifica navigator.webdriver, plugins, etc.
                await ctx.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt']});
                    window.chrome = {runtime: {}};
                """)

                page = await ctx.new_page()

                # Intercept API responses
                async def handle_response(response: Response) -> None:
                    if not any(pat in response.url for pat in self.API_PATTERNS):
                        return
                    if response.status != 200:
                        return
                    try:
                        ct = response.headers.get("content-type", "")
                        if "json" not in ct:
                            return
                        data = await response.json()
                        found = self._search_api_response(data, query_home, query_away)
                        collected_odds.extend(found)
                    except Exception:
                        pass

                page.on("response", handle_response)

                # Navega para a seção de futebol
                try:
                    await page.goto(
                        self.SOCCER_URL,
                        wait_until="domcontentloaded",
                        timeout=45_000,
                    )
                except PWTimeout:
                    logger.warning("[Bet365] Timeout na navegação. Prosseguindo mesmo assim.")

                # Delay humano antes de interagir
                await page.wait_for_timeout(random.randint(3_000, 5_500))

                # Tenta usar a caixa de busca para filtrar a partida
                if not collected_odds:
                    await self._try_search(page, match_query, collected_odds, query_home, query_away)

                # Fallback DOM se API e busca não funcionaram
                if not collected_odds:
                    logger.debug("[Bet365] Tentando fallback DOM...")
                    dom_odds = await self._fallback_dom(page, query_home, query_away)
                    collected_odds.extend(dom_odds)

                await browser.close()

        except PWTimeout:
            logger.error("[Bet365] Timeout geral ao carregar a Bet365.")
        except Exception as exc:
            logger.error(f"[Bet365] Erro inesperado: {exc}")

        logger.info(f"[Bet365] Odds coletadas: {len(collected_odds)}")
        return collected_odds

    def _search_api_response(self, data, query_home: str, query_away: str) -> list[dict]:
        """Parseia resposta da API interna da Bet365 em busca da partida alvo."""
        results = []
        events = []

        # A Bet365 usa estruturas variadas — tenta todas as conhecidas
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            events.extend(data.get("events", []))
            events.extend(data.get("fixtures", []))
            for k in ["data", "response", "result"]:
                v = data.get(k, {})
                if isinstance(v, list):
                    events.extend(v)
                elif isinstance(v, dict):
                    events.extend(v.get("events", []))

        for event in events:
            try:
                home = event.get("home", {}).get("name", "") or event.get("homeTeam", "")
                away = event.get("away", {}).get("name", "") or event.get("awayTeam", "")
                if not home or not away:
                    continue
                if not match_is_target(home, away, query_home, query_away):
                    continue
                odd = self._extract_odds_from_event(event, home, away)
                if odd:
                    results.append(odd)
            except Exception as exc:
                logger.debug(f"[Bet365][API] Erro ao processar evento: {exc}")

        return results

    def _extract_odds_from_event(self, event: dict, home: str, away: str) -> dict | None:
        """Extrai odds 1X2 de um evento da API interna."""
        try:
            markets = event.get("markets", []) or event.get("odds", [])
            for market in markets:
                selections = market.get("selections", []) or market.get("outcomes", [])
                if len(selections) != 3:
                    continue
                # Tenta extrair em ordem: home, draw, away
                vals = []
                for sel in selections:
                    price = sel.get("price") or sel.get("odd") or sel.get("odds")
                    if price:
                        vals.append(float(price))
                if len(vals) == 3:
                    return self.build_odd_payload(
                        bookmaker=self.BOOKMAKER_NAME,
                        match_id=build_match_id(home, away),
                        team_home=home,
                        team_away=away,
                        home_win=vals[0],
                        draw=vals[1],
                        away_win=vals[2],
                    )
        except Exception as exc:
            logger.debug(f"[Bet365][API] Erro ao extrair odds: {exc}")
        return None

    async def _try_search(
        self, page, query: str, collected: list, query_home: str, query_away: str
    ) -> None:
        """
        Usa a caixa de busca da Bet365 para filtrar a partida e esperar API responses.
        ⚠️ Seletor da search box é frágil.
        """
        try:
            search = page.locator(self.SEL_SEARCH_BOX).first
            if await search.count() == 0:
                return

            await search.click()
            await page.wait_for_timeout(random.randint(500, 1_000))
            # Digita com velocidade humana apenas o nome do time mandante
            await page.keyboard.type(query_home, delay=random.randint(80, 150))
            await page.wait_for_timeout(2_500)

            # As respostas de API são capturadas pelo handler de response
            logger.debug(f"[Bet365] Busca realizada: '{query_home}'")

        except Exception as exc:
            logger.debug(f"[Bet365] Busca falhou: {exc}")

    async def _fallback_dom(self, page, query_home: str, query_away: str) -> list[dict]:
        """
        Fallback DOM para quando a API não for interceptada.
        ⚠️ MUITO FRÁGIL — seletores mudam com cada deploy da Bet365.
        Verificar e atualizar periodicamente via DevTools.
        """
        results = []
        try:
            await page.wait_for_selector(self.SEL_EVENT_TEAMS, timeout=5_000)
            rows = await page.locator(self.SEL_EVENT_TEAMS).all()

            for row in rows:
                text = await row.inner_text()
                teams = [t.strip() for t in text.split("\n") if t.strip()]
                if len(teams) < 2:
                    continue

                home, away = teams[0], teams[1]
                if not match_is_target(home, away, query_home, query_away):
                    continue

                # Tenta pegar as odds no elemento ancestral do evento
                try:
                    parent = row.locator(
                        "xpath=ancestor::*[contains(@class,'rcl-ParticipantFixtureDetails') "
                        "or contains(@class,'sgl-EventContainer')]"
                    ).first
                    odd_btns = await parent.locator(self.SEL_ODD_BUTTON).all()

                    if len(odd_btns) >= 3:
                        home_win = float((await odd_btns[0].inner_text()).strip())
                        draw = float((await odd_btns[1].inner_text()).strip())
                        away_win = float((await odd_btns[2].inner_text()).strip())

                        results.append(self.build_odd_payload(
                            bookmaker=self.BOOKMAKER_NAME,
                            match_id=build_match_id(home, away),
                            team_home=home,
                            team_away=away,
                            home_win=home_win,
                            draw=draw,
                            away_win=away_win,
                        ))
                        break  # Encontrou a partida — para de iterar

                except (ValueError, IndexError) as exc:
                    logger.debug(f"[Bet365][DOM] Erro ao parsear odds: {exc}")

        except PWTimeout:
            logger.debug("[Bet365][DOM] Timeout esperando elementos.")
        except Exception as exc:
            logger.debug(f"[Bet365][DOM] Erro no fallback: {exc}")

        return results
