"""
extractors/base_extractor.py
-----------------------------
Classe abstrata que define a interface obrigatória para todos os extractors.

Todo extractor deve:
1. Herdar de BaseExtractor
2. Definir BOOKMAKER_NAME como atributo de classe
3. Implementar o método async extract(match_query)
4. Retornar lista de dicts no schema RawOddDTO (ou [] em falha)
5. NUNCA propagar exceção para fora — toda falha é logada e retorna []
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    Interface obrigatória para todos os extractors de casas de apostas.

    Cada extractor é stateless: recebe match_query, executa I/O, retorna lista de odds.
    A responsabilidade de publicar no Kafka é do scraper_runner, não do extractor.

    Schema de retorno obrigatório (RawOddDTO):
    {
        "bookmaker":  str,    # ex: "Bet365"
        "match_id":   str,    # ex: "real_madrid_v_barcelona"
        "team_home":  str,    # nome original do mandante
        "team_away":  str,    # nome original do visitante
        "odds": {
            "home_win": float,  # > 0
            "draw":     float,  # > 0
            "away_win": float   # > 0
        },
        "timestamp":  str     # ISO-8601 UTC, ex: "2026-04-23T21:00:00Z"
    }
    """

    # Subclasses DEVEM sobrescrever com o nome exato da casa (ex: "Bet365")
    BOOKMAKER_NAME: str = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Validação em tempo de definição da subclasse
        if not cls.BOOKMAKER_NAME and not getattr(cls, "__abstractmethods__", None):
            raise TypeError(
                f"{cls.__name__} deve definir o atributo de classe BOOKMAKER_NAME"
            )

    @abstractmethod
    async def extract(self, match_query: str) -> list[dict]:
        """
        Busca odds para a partida especificada na casa de apostas.

        Args:
            match_query: String fornecida pelo usuário (ex: "Flamengo x Vasco").
                         Use utils.match_id.parse_match_query() para separar os times.

        Returns:
            Lista de dicts no schema RawOddDTO.
            Retorna [] se a partida não for encontrada ou ocorrer qualquer erro.
            NUNCA levanta exceção.
        """
        ...

    @staticmethod
    def now_iso() -> str:
        """Retorna o timestamp atual em ISO-8601 UTC no formato esperado pelo backend."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def build_odd_payload(
        bookmaker: str,
        match_id: str,
        team_home: str,
        team_away: str,
        home_win: float,
        draw: float,
        away_win: float,
    ) -> dict:
        """
        Constrói o payload final no schema RawOddDTO.

        Valida que todos os valores de odds são positivos antes de construir.

        Args:
            bookmaker: Nome da casa de apostas
            match_id:  ID canônico da partida (gerado por build_match_id)
            team_home: Nome do mandante (original, não normalizado)
            team_away: Nome do visitante (original, não normalizado)
            home_win:  Odd para vitória do mandante
            draw:      Odd para empate
            away_win:  Odd para vitória do visitante

        Returns:
            Dict no schema RawOddDTO pronto para publicação no Kafka.

        Raises:
            ValueError: Se qualquer odd for <= 0 ou se campos obrigatórios estiverem vazios.
        """
        if not all([bookmaker.strip(), match_id.strip(), team_home.strip(), team_away.strip()]):
            raise ValueError("Campos bookmaker, match_id, team_home e team_away são obrigatórios")

        if home_win <= 0 or draw <= 0 or away_win <= 0:
            raise ValueError(
                f"Todas as odds devem ser > 0. "
                f"Recebido: home_win={home_win}, draw={draw}, away_win={away_win}"
            )

        return {
            "bookmaker": bookmaker,
            "match_id": match_id,
            "team_home": team_home,
            "team_away": team_away,
            "odds": {
                "home_win": round(float(home_win), 4),
                "draw": round(float(draw), 4),
                "away_win": round(float(away_win), 4),
            },
            "timestamp": BaseExtractor.now_iso(),
        }
