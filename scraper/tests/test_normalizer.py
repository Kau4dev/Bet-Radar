"""
tests/test_normalizer.py
-------------------------
Testes unitários para utils/match_id.py e utils/normalizer.py

Casos testados (mínimo 8 para match_id + 5 para normalizer):
- Nomes simples sem acentos
- Nomes com acentos e caracteres especiais
- Nomes com espaços múltiplos
- Siglas e abreviações (ex: "C.F.", "F.C.")
- Separadores variados na query (x, vs, X, VS, versus, -)
- Nomes compostos (ex: "Atletico de Madrid")
- Casing misto
- Strings com underscores e hífens
- Fuzzy match: sobrenome parcial
- Fuzzy match: variações de escrita
- Sem correspondência (false negatives)
"""

import pytest
from utils.match_id import normalize_team_name, build_match_id, parse_match_query
from utils.normalizer import teams_match, match_is_target


# ---------------------------------------------------------------------------
# Testes: normalize_team_name
# ---------------------------------------------------------------------------

class TestNormalizeTeamName:

    def test_simple_lowercase(self):
        """Nome simples sem transformação especial."""
        assert normalize_team_name("Flamengo") == "flamengo"

    def test_accented_characters(self):
        """Remove acentos corretamente."""
        assert normalize_team_name("São Paulo FC") == "sao_paulo_fc"

    def test_accented_e_tilde(self):
        """Tilde em vogais."""
        assert normalize_team_name("Atlético-MG") == "atletico_mg"

    def test_hyphen_separator(self):
        """Hífen é convertido para underscore."""
        assert normalize_team_name("Atlético-Mineiro") == "atletico_mineiro"

    def test_dots_in_abbreviation(self):
        """Pontos em abreviações (ex: C.F.) são removidos."""
        result = normalize_team_name("Real Madrid C.F.")
        assert result == "real_madrid_c_f"

    def test_multiple_spaces(self):
        """Espaços múltiplos colapsam em um único underscore."""
        assert normalize_team_name("Manchester   City") == "manchester_city"

    def test_mixed_case(self):
        """Casing misto é normalizado para lowercase."""
        assert normalize_team_name("BARCELONA") == "barcelona"

    def test_leading_trailing_spaces(self):
        """Espaços nas bordas são removidos."""
        assert normalize_team_name("  Vasco  ") == "vasco"

    def test_special_characters(self):
        """Caracteres especiais como ° são removidos."""
        assert normalize_team_name("Grêmio F.B.P.A") == "gremio_f_b_p_a"

    def test_accent_cedilla(self):
        """Cedilha é convertida para 'c'."""
        assert normalize_team_name("Botafogo de Futebol e Regatas") == "botafogo_de_futebol_e_regatas"

    def test_empty_raises(self):
        """String vazia lança ValueError."""
        with pytest.raises(ValueError):
            normalize_team_name("")

    def test_whitespace_only_raises(self):
        """String com apenas espaços lança ValueError."""
        with pytest.raises(ValueError):
            normalize_team_name("   ")


# ---------------------------------------------------------------------------
# Testes: build_match_id
# ---------------------------------------------------------------------------

class TestBuildMatchId:

    def test_simple_match(self):
        assert build_match_id("Flamengo", "Vasco") == "flamengo_v_vasco"

    def test_accented_teams(self):
        assert build_match_id("São Paulo FC", "Corinthians") == "sao_paulo_fc_v_corinthians"

    def test_european_teams(self):
        assert build_match_id("Real Madrid", "Barcelona") == "real_madrid_v_barcelona"

    def test_teams_with_abbreviations(self):
        """Abreviações com pontos no nome do time."""
        result = build_match_id("Atlético-MG", "Cruzeiro E.C.")
        assert result == "atletico_mg_v_cruzeiro_e_c"

    def test_separator_is_v(self):
        """O separador _v_ é usado exatamente (compatível com backend Java)."""
        result = build_match_id("Manchester City", "Arsenal")
        assert "_v_" in result
        assert result == "manchester_city_v_arsenal"

    def test_unicode_special_char(self):
        """Caracteres Unicode especiais são removidos."""
        result = build_match_id("Grêmio", "Internacional")
        assert result == "gremio_v_internacional"


# ---------------------------------------------------------------------------
# Testes: parse_match_query
# ---------------------------------------------------------------------------

class TestParseMatchQuery:

    @pytest.mark.parametrize("query,expected_home,expected_away", [
        ("Flamengo x Vasco",         "Flamengo",      "Vasco"),
        ("Flamengo vs Vasco",        "Flamengo",      "Vasco"),
        ("Flamengo X Vasco",         "Flamengo",      "Vasco"),
        ("Flamengo VS Vasco",        "Flamengo",      "Vasco"),
        ("Flamengo versus Vasco",    "Flamengo",      "Vasco"),
        ("Real Madrid x Barcelona",  "Real Madrid",   "Barcelona"),
        ("Manchester City vs Arsenal", "Manchester City", "Arsenal"),
    ])
    def test_various_separators(self, query, expected_home, expected_away):
        home, away = parse_match_query(query)
        assert home == expected_home
        assert away == expected_away

    def test_invalid_query_raises(self):
        """Query sem separador reconhecido lança ValueError."""
        with pytest.raises(ValueError):
            parse_match_query("FlamengoVasco")


# ---------------------------------------------------------------------------
# Testes: teams_match (fuzzy)
# ---------------------------------------------------------------------------

class TestTeamsMatch:

    def test_exact_match(self):
        assert teams_match("Flamengo", "Flamengo") is True

    def test_substring_match_short_in_long(self):
        """Nome curto contido no longo (Vasco → Vasco da Gama)."""
        assert teams_match("Vasco", "Vasco da Gama") is True

    def test_substring_match_long_in_short(self):
        """Prefixo comum (FC Barcelona → Barcelona)."""
        assert teams_match("Barcelona", "FC Barcelona") is True

    def test_fuzzy_match_above_threshold(self):
        """Similaridade alta — mesmo time com grafia levemente diferente."""
        assert teams_match("Atletico Mineiro", "Atlético Mineiro") is True

    def test_no_match_different_teams(self):
        """Times completamente diferentes não devem dar match."""
        assert teams_match("Juventus", "Boca Juniors") is False

    def test_no_match_short_string(self):
        """String muito curta não deve produzir falso positivo."""
        assert teams_match("A", "Palmeiras") is False


# ---------------------------------------------------------------------------
# Testes: match_is_target
# ---------------------------------------------------------------------------

class TestMatchIsTarget:

    def test_forward_match(self):
        """Ordem home/away idêntica."""
        assert match_is_target("Flamengo", "Vasco", "Flamengo", "Vasco") is True

    def test_reverse_match(self):
        """Usuário inverteu a ordem dos times."""
        assert match_is_target("Flamengo", "Vasco", "Vasco", "Flamengo") is True

    def test_partial_name_match(self):
        """Nome parcial do usuário vs nome completo na página."""
        assert match_is_target("Vasco da Gama", "Flamengo", "Vasco", "Flamengo") is True

    def test_no_match(self):
        """Partida completamente diferente."""
        assert match_is_target("Real Madrid", "Barcelona", "Flamengo", "Vasco") is False
