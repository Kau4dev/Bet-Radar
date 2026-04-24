"""
extractors/betano.py
---------------------
Extractor para Betano via Playwright + intercepção de respostas de rede.

Estratégia:
    1. Abre o Playwright (headless Chromium)
    2. Navega para a página de futebol da Betano Brasil
    3. Intercepts todas as respostas da API interna (padrão: /api/v1.0/*)
    4. Parseia os eventos retornados buscando a partida alvo
    5. Extrai as odds do mercado 1X2

A API interna da Betano retorna JSON com estrutura de eventos e mercados.
Os seletores CSS são usados como fallback caso a API mude.

Anti-bot:
    - playwright-stealth para mascarar automação
    - User-Agent realista
    - Locale e timezone configurados como BR
    - Delay aleatório entre ações
"""

import asyncio
import logging
import random

from playwright.async_api import async_playwright, Response, TimeoutError as PWTimeout

from extractors.base_extractor import BaseExtractor
from utils.match_id import build_match_id, parse_match_query
from utils.normalizer import match_is_target

logger = logging.getLogger(__name__)


class BetanoExtractor(BaseExtractor):
    """
    Extractor de odds da Betano Brasil usando intercepção de rede via Playwright.

    Funciona interceptando as chamadas de API que o front-end da Betano faz ao
    carregar a lista de eventos. Isso é mais estável que parsear o DOM diretamente.
    """

    BOOKMAKER_NAME = "Betano"
    BASE_URL = "https://br.betano.com"
    SOCCER_URL = "https://br.betano.com/sport/futebol/"

    # Padrões de URL da API interna da Betano (identificados via DevTools > Network)
    API_PATTERNS = [
        "/api/v1.0/",
        "/api/sports/",
        "betano.com/api/",
    ]

    # Seletores CSS como fallback (frágeis — classes React geradas dinamicamente)
    # ⚠️ FRÁGIL: classes React mudam a cada deploy. Atualizar se parar de funcionar.
    SEL_EVENT_NAME = "[class*='events-list__game']"
    SEL_ODD_VALUE = "[class*='selections__odd-value'], [data-qa='odd-value']"

    async def extract(self, match_query: str) -> list[dict]:
        """
        Busca odds para a partida informada na Betano Brasil.

        Args:
            match_query: Ex: "Flamengo x Vasco"

        Returns:
            Lista com 0 ou mais dicts no schema RawOddDTO.
        """
        try:
            query_home, query_away = parse_match_query(match_query)
        except ValueError as exc:
            logger.warning(f"[Betano] Query inválida: {exc}")
            return []

        logger.info(f"[Betano] Buscando: {query_home} x {query_away}")

        collected_odds: list[dict] = []

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-extensions",
                    ],
                )
                ctx = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="pt-BR",
                    timezone_id="America/Sao_Paulo",
                    viewport={"width": 1366, "height": 768},
                )
                page = await ctx.new_page()

                # Intercepta respostas da API interna da Betano
                async def handle_api_response(response: Response) -> None:
                    if not any(pat in response.url for pat in self.API_PATTERNS):
                        return
                    if response.status != 200:
                        return
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "json" not in content_type:
                            return
                        data = await response.json()
                        found = self._search_events(data, query_home, query_away)
                        collected_odds.extend(found)
                    except Exception as exc:
                        logger.debug(f"[Betano] Erro ao parsear resposta API: {exc}")

                page.on("response", handle_api_response)

                # Navega para a página de futebol
                await page.goto(
                    self.SOCCER_URL,
                    wait_until="networkidle",
                    timeout=30_000,
                )

                # Aguarda carregamento adicional (lazy loading de eventos)
                await page.wait_for_timeout(random.randint(2_500, 4_000))

                # Se nada foi coletado via API, tenta fallback por DOM
                if not collected_odds:
                    logger.debug("[Betano] API não retornou dados. Tentando fallback DOM...")
                    dom_odds = await self._fallback_dom(page, query_home, query_away)
                    collected_odds.extend(dom_odds)

                await browser.close()

        except PWTimeout:
            logger.error("[Betano] Timeout ao carregar a página.")
        except Exception as exc:
            logger.error(f"[Betano] Erro inesperado: {exc}")

        logger.info(f"[Betano] Odds coletadas: {len(collected_odds)}")
        return collected_odds

    def _search_events(self, data: dict | list, query_home: str, query_away: str) -> list[dict]:
        """
        Percorre a estrutura JSON retornada pela API da Betano buscando a partida alvo.

        A API da Betano pode retornar dados em diferentes formatos dependendo
        do endpoint. Esta função tenta múltiplas estruturas conhecidas.
        """
        results = []

        # Tenta extrair lista de eventos de diferentes estruturas conhecidas
        events = []
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            # Estrutura 1: {"data": {"blocks": [{"events": [...]}]}}
            for block in data.get("data", {}).get("blocks", []):
                events.extend(block.get("events", []))
            # Estrutura 2: {"data": {"events": [...]}}
            events.extend(data.get("data", {}).get("events", []))
            # Estrutura 3: {"events": [...]}
            events.extend(data.get("events", []))
            # Estrutura 4: raiz é lista de eventos diretos
            if not events and "home_team" in data:
                events = [data]

        for event in events:
            try:
                home = (
                    event.get("home_team")
                    or event.get("homeTeam")
                    or event.get("home", {}).get("name", "")
                )
                away = (
                    event.get("away_team")
                    or event.get("awayTeam")
                    or event.get("away", {}).get("name", "")
                )

                if not home or not away:
                    continue
                if not match_is_target(home, away, query_home, query_away):
                    continue

                odd = self._parse_markets(event, home, away)
                if odd:
                    results.append(odd)

            except Exception as exc:
                logger.debug(f"[Betano] Erro ao processar evento: {exc}")

        return results

    def _parse_markets(self, event: dict, home: str, away: str) -> dict | None:
        """
        Extrai as odds do mercado 1X2 (resultado final) de um evento Betano.

        A Betano usa diferentes nomes para o mercado 1X2:
        '1X2', 'Resultado Final', 'Match Result', 'Full Time Result'
        """
        markets = event.get("markets", [])

        # Nomes conhecidos para o mercado 1X2 na Betano
        market_names_1x2 = {"1X2", "1x2", "Resultado Final", "Match Result", "Full Time Result"}

        target_market = None
        for market in markets:
            name = market.get("name", "")
            if name in market_names_1x2:
                target_market = market
                break

        # Fallback: pega o primeiro mercado com 3 seleções (provavelmente 1X2)
        if not target_market:
            for market in markets:
                if len(market.get("selections", [])) == 3:
                    target_market = market
                    break

        if not target_market:
            return None

        selections = target_market.get("selections", [])
        try:
            # As seleções podem ter nomes "1", "X", "2" ou "Home", "Draw", "Away"
            home_win_sel = next(
                s for s in selections
                if s.get("name") in {"1", "Home", "Casa", "home"}
            )
            draw_sel = next(
                s for s in selections
                if s.get("name") in {"X", "Draw", "Empate", "draw"}
            )
            away_win_sel = next(
                s for s in selections
                if s.get("name") in {"2", "Away", "Visitante", "away"}
            )

            home_win = float(home_win_sel.get("odd") or home_win_sel.get("price") or 0)
            draw = float(draw_sel.get("odd") or draw_sel.get("price") or 0)
            away_win = float(away_win_sel.get("odd") or away_win_sel.get("price") or 0)

            return self.build_odd_payload(
                bookmaker=self.BOOKMAKER_NAME,
                match_id=build_match_id(home, away),
                team_home=home,
                team_away=away,
                home_win=home_win,
                draw=draw,
                away_win=away_win,
            )

        except (StopIteration, ValueError, TypeError) as exc:
            logger.debug(f"[Betano] Não foi possível extrair 1X2: {exc}")
            return None

    async def _fallback_dom(self, page, query_home: str, query_away: str) -> list[dict]:
        """
        Fallback: tenta extrair odds diretamente do DOM quando a intercepção de API falha.

        ⚠️ FRÁGIL: seletores CSS mudam com frequência. Verificar periodicamente.
        """
        results = []
        try:
            # Aguarda ao menos um evento aparecer no DOM
            await page.wait_for_selector(self.SEL_EVENT_NAME, timeout=5_000)
            event_elements = await page.locator(self.SEL_EVENT_NAME).all()

            for el in event_elements:
                text = await el.inner_text()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if len(lines) < 2:
                    continue

                home = lines[0]
                away = lines[1]
                if not match_is_target(home, away, query_home, query_away):
                    continue

                # Tenta pegar as 3 odds (1, X, 2) do elemento pai
                try:
                    parent = el.locator("xpath=ancestor::*[contains(@class,'game')]").first
                    odd_els = await parent.locator(self.SEL_ODD_VALUE).all()
                    if len(odd_els) >= 3:
                        home_win = float((await odd_els[0].inner_text()).strip())
                        draw = float((await odd_els[1].inner_text()).strip())
                        away_win = float((await odd_els[2].inner_text()).strip())
                        odd = self.build_odd_payload(
                            bookmaker=self.BOOKMAKER_NAME,
                            match_id=build_match_id(home, away),
                            team_home=home,
                            team_away=away,
                            home_win=home_win,
                            draw=draw,
                            away_win=away_win,
                        )
                        results.append(odd)
                except Exception as exc:
                    logger.debug(f"[Betano][DOM] Erro ao extrair odds do DOM: {exc}")

        except PWTimeout:
            logger.debug("[Betano][DOM] Timeout aguardando elementos DOM.")
        except Exception as exc:
            logger.debug(f"[Betano][DOM] Erro no fallback DOM: {exc}")

        return results
