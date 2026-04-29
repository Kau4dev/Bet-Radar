"""
utils/normalizer.py
-------------------
Comparação fuzzy de nomes de times usando difflib.SequenceMatcher.

Utilizado pelos extractors para decidir se um resultado de busca corresponde
à partida solicitada pelo usuário, mesmo com grafias levemente diferentes.

Exemplos de correspondências esperadas:
    "Real Madrid" ↔ "Real Madrid CF"           → match (substring)
    "Flamengo"    ↔ "Clube de Regatas Flamengo" → match (substring)
    "Vasco"       ↔ "Vasco da Gama"             → match (fuzzy ≥ 0.75)
    "Barcelona"   ↔ "FC Barcelona"              → match (substring)
    "Juventus"    ↔ "Boca Juniors"              → NO match
"""

import difflib
from utils.match_id import normalize_team_name

# Threshold mínimo para considerar dois nomes como sendo o mesmo time.
# Valor 0.75 foi calibrado empiricamente para o mercado de futebol.
SIMILARITY_THRESHOLD = 0.75


def teams_match(query_name: str, candidate_name: str, threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """
    Verifica se dois nomes de times se referem ao mesmo time.

    Estratégia em camadas (ordem de custo crescente):
        1. Igualdade exata após normalização (mais rápido)
        2. Substring: um contém o outro após normalização
        3. Similaridade fuzzy via SequenceMatcher (mais lento, usado como fallback)

    Args:
        query_name: Nome fornecido pelo usuário (ex: "Vasco")
        candidate_name: Nome encontrado na página da casa de aposta (ex: "Vasco da Gama")
        threshold: Razão mínima de similaridade (0.0 a 1.0). Padrão: 0.75

    Returns:
        True se os nomes correspondem ao mesmo time.

    Exemplos:
        >>> teams_match("Vasco", "Vasco da Gama")
        True
        >>> teams_match("Barcelona", "FC Barcelona")
        True
        >>> teams_match("Juventus", "Boca Juniors")
        False
    """
    norm_query = normalize_team_name(query_name)
    norm_candidate = normalize_team_name(candidate_name)

    # 1. Igualdade exata
    if norm_query == norm_candidate:
        return True

    # 2. Substring bidirecional (um contém o outro)
    if norm_query in norm_candidate or norm_candidate in norm_query:
        # Proteção contra falsos positivos em nomes muito curtos (ex: "A" em "Palmeiras")
        if len(norm_query) >= 3 and len(norm_candidate) >= 3:
            return True

    # 3. Similaridade fuzzy (SequenceMatcher)
    ratio = difflib.SequenceMatcher(None, norm_query, norm_candidate).ratio()
    return ratio >= threshold


def match_is_target(
    home_in_page: str,
    away_in_page: str,
    query_home: str,
    query_away: str,
    threshold: float = SIMILARITY_THRESHOLD,
) -> bool:
    """
    Verifica se uma partida encontrada em uma página corresponde à partida buscada.

    Testa as duas direções:
        - home_page ↔ query_home  E  away_page ↔ query_away
        - home_page ↔ query_away  E  away_page ↔ query_home (ordem invertida)

    Args:
        home_in_page: Nome do mandante conforme exibido na casa de apostas
        away_in_page: Nome do visitante conforme exibido na casa de apostas
        query_home: Nome do mandante fornecido pelo usuário
        query_away: Nome do visitante fornecido pelo usuário
        threshold: Threshold de similaridade fuzzy

    Returns:
        True se a partida corresponde (em qualquer ordem)
    """
    # Direção natural: home=home, away=away
    forward = (
        teams_match(query_home, home_in_page, threshold)
        and teams_match(query_away, away_in_page, threshold)
    )
    if forward:
        return True

    # Direção invertida: usuário pode ter invertido a ordem
    reverse = (
        teams_match(query_home, away_in_page, threshold)
        and teams_match(query_away, home_in_page, threshold)
    )
    return reverse
