"""
utils/match_id.py
-----------------
Gera o match_id canônico compatível com o backend Java.

O backend (OddProcessorService.java) gera:
    universalMatchId = cleanTeamHome + "_v_" + cleanTeamAway

onde cleanTeamHome/Away são normalizados por TeamNormalizationService.
Este módulo replica exatamente a mesma lógica em Python.
"""

import re
import unicodedata


def normalize_team_name(name: str) -> str:
    """
    Normaliza o nome de um time para uso no match_id canônico.

    Passos:
        1. Remove acentos via decomposição NFKD (é → e, ã → a, etc.)
        2. Converte para ASCII puro
        3. Lowercase
        4. Substitui qualquer sequência de caracteres não-alfanuméricos por '_'
        5. Remove underscores duplicados e nas bordas

    Args:
        name: Nome original do time (ex: "São Paulo FC", "Real Madrid C.F.")

    Returns:
        Nome normalizado (ex: "sao_paulo_fc", "real_madrid_c_f")

    Exemplos:
        >>> normalize_team_name("Flamengo")
        'flamengo'
        >>> normalize_team_name("São Paulo FC")
        'sao_paulo_fc'
        >>> normalize_team_name("Atlético-MG")
        'atletico_mg'
        >>> normalize_team_name("Real Madrid C.F.")
        'real_madrid_c_f'
    """
    if not name or not name.strip():
        raise ValueError(f"Nome do time não pode ser vazio: {name!r}")

    # 1. Normalização Unicode NFKD (decompõe caracteres acentuados)
    nfkd_form = unicodedata.normalize("NFKD", name.strip())

    # 2. Codifica em ASCII ignorando caracteres não-representáveis (remove acentos)
    ascii_bytes = nfkd_form.encode("ASCII", "ignore")
    ascii_str = ascii_bytes.decode("ASCII")

    # 3. Lowercase
    lower = ascii_str.lower()

    # 4. Substitui qualquer sequência de caracteres não-alfanuméricos por '_'
    with_underscores = re.sub(r"[^a-z0-9]+", "_", lower)

    # 5. Remove underscores duplicados e nas bordas
    clean = re.sub(r"_+", "_", with_underscores).strip("_")

    return clean


def build_match_id(team_home: str, team_away: str) -> str:
    """
    Constrói o match_id canônico no formato esperado pelo backend Java.

    Formato: {home_normalizado}_v_{away_normalizado}

    Args:
        team_home: Nome do time mandante
        team_away: Nome do time visitante

    Returns:
        match_id canônico (ex: "flamengo_v_vasco_da_gama")

    Exemplos:
        >>> build_match_id("Flamengo", "Vasco da Gama")
        'flamengo_v_vasco_da_gama'
        >>> build_match_id("Real Madrid", "Barcelona")
        'real_madrid_v_barcelona'
    """
    home_normalized = normalize_team_name(team_home)
    away_normalized = normalize_team_name(team_away)
    return f"{home_normalized}_v_{away_normalized}"


def parse_match_query(query: str) -> tuple[str, str]:
    """
    Extrai os nomes dos times de uma query fornecida pelo usuário.

    Suporta múltiplos separadores: ' x ', ' vs ', ' X ', ' VS ', ' versus ', ' - '

    Args:
        query: String fornecida pelo usuário (ex: "Flamengo x Vasco")

    Returns:
        Tupla (team_home, team_away)

    Raises:
        ValueError: Se não for possível identificar o separador

    Exemplos:
        >>> parse_match_query("Real Madrid x Barcelona")
        ('Real Madrid', 'Barcelona')
        >>> parse_match_query("Flamengo vs Vasco")
        ('Flamengo', 'Vasco')
    """
    separators = [" x ", " vs ", " X ", " VS ", " versus ", " Versus ", " - "]
    for sep in separators:
        if sep in query:
            parts = query.split(sep, 1)
            home = parts[0].strip()
            away = parts[1].strip()
            if home and away:
                return home, away

    # Última tentativa: split por hífen simples (sem espaços)
    if "-" in query and " " in query:
        idx = query.index("-")
        home = query[:idx].strip()
        away = query[idx + 1:].strip()
        if home and away:
            return home, away

    raise ValueError(
        f"Não foi possível identificar os times na query: {query!r}. "
        "Use formatos como 'Time A x Time B' ou 'Time A vs Time B'."
    )
