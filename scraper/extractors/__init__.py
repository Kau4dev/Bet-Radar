"""
extractors/__init__.py
-----------------------
Exporta todos os extractors disponíveis para uso pelo scraper_runner.
"""

from extractors.base_extractor import BaseExtractor
from extractors.pinnacle import PinnacleExtractor
from extractors.betano import BetanoExtractor
from extractors.bet365 import Bet365Extractor
from extractors.sportingbet import SportingbetExtractor
from extractors.superbet import SuperbetExtractor

# Lista canônica de extractors ativos — scraper_runner itera sobre esta lista
ALL_EXTRACTORS: list[BaseExtractor] = [
    PinnacleExtractor(),
    BetanoExtractor(),
    Bet365Extractor(),
    SportingbetExtractor(),
    SuperbetExtractor(),
]

__all__ = [
    "BaseExtractor",
    "PinnacleExtractor",
    "BetanoExtractor",
    "Bet365Extractor",
    "SportingbetExtractor",
    "SuperbetExtractor",
    "ALL_EXTRACTORS",
]
