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
                is_headless = os.getenv("SHOW_BROWSER") != "1"
                launch_args = {
                    "headless": is_headless,
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
                page = await ctx.new_page()

                # Usa a biblioteca dedicada playwright-stealth para mascarar a automação
                # de forma muito mais profunda (WebGL, Canvas, navigator.webdriver, etc.)
                try:
                    from playwright_stealth import stealth_async
                    await stealth_async(page)
                    logger.debug("[Bet365] playwright-stealth aplicado com sucesso.")
                except ImportError:
                    logger.warning("[Bet365] playwright-stealth não instalado. Usando fallback stealth fraco.")
                    # Fallback fraco caso a lib não esteja instalada
                    await ctx.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.chrome = {runtime: {}};
                    """)

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
                    # 'commit' faz com que não fique preso na tela de loading do Cloudflare/Bet365
                    await page.goto(
                        self.SOCCER_URL,
                        wait_until="commit",
                        timeout=30_000,
                    )
                except Exception as exc:
                    logger.warning(f"[Bet365] Erro na navegação: {exc}")
                    if not is_headless:
                        logger.warning("[Bet365] Pausando por 10s para debug visual da falha de rede...")
                        await page.wait_for_timeout(10_000)

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

                if not collected_odds and not is_headless:
                    logger.debug("[Bet365] ⚠️ Nenhuma odd coletada. Mantendo o navegador aberto por 15s para debug visual.")
                    await page.wait_for_timeout(15_000)

                await browser.close()

        except Exception as exc:
            logger.error(f"[Bet365] Erro fatal no script: {exc}")
            # Em caso de crash duro no Playwright, não podemos dar wait_for_timeout se o browser caiu,
            # mas o try/except mais genérico no page.goto já vai ajudar a pegar os problemas de rede.

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
        Aplica locators mais genéricos para lidar com a ofuscação das classes CSS.
        """
        try:
            # 1. Tenta clicar no ícone de lupa (frequentemente presente no header)
            search_icon = page.locator("[class*='Search'], [class*='search']").filter(has=page.locator("svg")).first
            if await search_icon.is_visible(timeout=2_000):
                await search_icon.click()
                await page.wait_for_timeout(1_000)

            # 2. Localiza o campo de input de texto ativo
            search_input = page.locator("input[type='text']").first
            if await search_input.is_visible(timeout=2_000):
                await search_input.click()
                await page.wait_for_timeout(500)
                
                # Digita o nome do time da casa pausadamente
                for char in query_home:
                    await search_input.type(char, delay=random.randint(50, 150))
                
                await page.wait_for_timeout(3_000)
                logger.debug(f"[Bet365] Busca realizada por: '{query_home}'")
            else:
                logger.debug("[Bet365] Caixa de busca não encontrada na tela.")

        except Exception as exc:
            logger.debug(f"[Bet365] Falha na rotina de busca: {exc}")

    async def _fallback_dom(self, page, query_home: str, query_away: str) -> list[dict]:
        """
        Fallback DOM para quando a API não for interceptada.
        A Bet365 ofusca fortemente as classes CSS (ex: cpr-29, rgl-542d6e).
        Usamos uma heurística via JavaScript que ignora classes e busca 
        o menor container que possua o nome dos dois times e os valores das odds.
        """
        results = []
        try:
            # Aguarda o DOM carregar minimamente
            await page.wait_for_timeout(2_000)

            # Injeta e executa JS para encontrar o bloco da partida
            js_script = """
            (args) => {
                const home = args.home;
                const away = args.away;
                const containers = Array.from(document.querySelectorAll('div, section, article, li'));
                
                let bestLines = null;
                let minLen = Infinity;

                for (let c of containers) {
                    let txt = c.innerText || "";
                    // Verifica se o container possui o nome de ambos os times
                    if (txt.includes(home) && txt.includes(away)) {
                        let lines = txt.split('\\n').map(l => l.trim()).filter(l => l);
                        // Filtra linhas que parecem ser odds (ex: 1.50, 3.60)
                        let decimals = lines.filter(l => /^\\d+\\.\\d{2,3}$/.test(l));
                        
                        // O bloco de evento costuma ter no mínimo 3 odds (1, X, 2)
                        if (decimals.length >= 3 && txt.length < minLen) {
                            minLen = txt.length;
                            bestLines = lines;
                        }
                    }
                }
                return bestLines;
            }
            """
            
            lines = await page.evaluate(js_script, {"home": query_home, "away": query_away})
            
            if not lines:
                logger.debug(f"[Bet365][DOM] Nenhum bloco encontrado para {query_home} x {query_away}")
                return []

            home_win, draw, away_win = 0.0, 0.0, 0.0
            
            # Tenta encontrar a âncora padrão "1", "X", "2"
            try:
                if "1" in lines and "X" in lines and "2" in lines:
                    home_win = float(lines[lines.index("1") + 1])
                    draw = float(lines[lines.index("X") + 1])
                    away_win = float(lines[lines.index("2") + 1])
                else:
                    raise ValueError("Marcadores 1, X, 2 não encontrados.")
            except (ValueError, IndexError):
                # Fallback: pega os últimos 3 números decimais (geralmente são 1, X, 2)
                import re
                decimals = [float(l) for l in lines if re.match(r"^\d+\.\d{2,3}$", l)]
                if len(decimals) >= 3:
                    home_win, draw, away_win = decimals[-3], decimals[-2], decimals[-1]
                else:
                    logger.debug("[Bet365][DOM] Não foi possível extrair os 3 valores numéricos.")
                    return []

            odd_payload = self.build_odd_payload(
                bookmaker=self.BOOKMAKER_NAME,
                match_id=build_match_id(query_home, query_away),
                team_home=query_home,
                team_away=query_away,
                home_win=home_win,
                draw=draw,
                away_win=away_win,
            )
            results.append(odd_payload)
            logger.debug("[Bet365][DOM] Odds extraídas com sucesso ignorando classes CSS.")

        except PWTimeout:
            logger.debug("[Bet365][DOM] Timeout aguardando renderização.")
        except Exception as exc:
            logger.debug(f"[Bet365][DOM] Erro na heurística de fallback: {exc}")

        return results
