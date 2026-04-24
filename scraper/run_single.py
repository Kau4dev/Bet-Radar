import asyncio
import argparse
import json
import os
from dotenv import load_dotenv

# Carrega as variáveis do .env (como ODDS_API_KEY)
load_dotenv()

from extractors.pinnacle import PinnacleExtractor
from extractors.betano import BetanoExtractor
from extractors.bet365 import Bet365Extractor
from extractors.sportingbet import SportingbetExtractor
from extractors.superbet import SuperbetExtractor

# Mapeamento dos extractors disponíveis
EXTRACTORS = {
    "pinnacle": PinnacleExtractor,
    "betano": BetanoExtractor,
    "bet365": Bet365Extractor,
    "sportingbet": SportingbetExtractor,
    "superbet": SuperbetExtractor,
}

async def test_extractor(extractor_name: str, match_query: str):
    extractor_class = EXTRACTORS.get(extractor_name.lower())
    if not extractor_class:
        print(f"❌ Extractor '{extractor_name}' não encontrado.")
        print(f"Opções válidas: {', '.join(EXTRACTORS.keys())}")
        return

    print(f"🚀 Iniciando teste do extractor: {extractor_class.BOOKMAKER_NAME}")
    print(f"🔍 Buscando partida: '{match_query}'")
    print("-" * 50)
    
    extractor = extractor_class()
    
    try:
        results = await extractor.extract(match_query)
        
        print(f"\n✅ Scraping finalizado. {len(results)} odd(s) encontrada(s).")
        if results:
            print("\nResultados (JSON):")
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print("Nenhuma odd encontrada. Verifique se a partida existe na casa de aposta ou se a query está correta.")
            
    except Exception as e:
        print(f"\n💥 Ocorreu um erro ao executar o extractor: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Testar um scraper individualmente.")
    parser.add_argument("extractor", help=f"Nome da casa (ex: {', '.join(EXTRACTORS.keys())})")
    parser.add_argument("match", help="Nome da partida (ex: 'Flamengo x Vasco')")
    parser.add_argument("--show-browser", action="store_true", help="Abre o navegador visivelmente (para debugar)")
    
    args = parser.parse_args()
    
    if args.show_browser:
        os.environ["SHOW_BROWSER"] = "1"
    
    # Rodar o loop assíncrono
    asyncio.run(test_extractor(args.extractor, args.match))
