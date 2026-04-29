package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class TeamNormalizationServiceTest {

    private final TeamNormalizationService service = new TeamNormalizationService();

    @Nested
    class Normalize {

        @Test
        @DisplayName("Deve normalizar apelidos conhecidos")
        void deveNormalizarApelidosConhecidos() {
            assertEquals("Real Madrid", service.normalize("r. madrid"));
            assertEquals("Barcelona", service.normalize("barca"));
            assertEquals("Sao Paulo", service.normalize("spfc"));
        }

        @Test
        @DisplayName("Deve normalizar com trim e lowercase")
        void deveNormalizarComTrimELowercase() {
            assertEquals("Real Madrid", service.normalize("  REAL MADRID FC  "));
        }

        @Test
        @DisplayName("Deve capitalizar quando nao houver alias")
        void deveCapitalizarQuandoNaoHouverAlias() {
            assertEquals("Liverpool", service.normalize("liverpool"));
        }

        @Test
        @DisplayName("Deve lancar excecao quando nome for nulo")
        void deveLancarExcecaoQuandoNomeForNulo() {
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.normalize(null));
            assertEquals("Nome do time nao pode ser nulo", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao quando nome for vazio")
        void deveLancarExcecaoQuandoNomeForVazio() {
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.normalize("   "));
            assertEquals("Nome do time nao pode ser nulo", ex.getMessage());
        }
    }
}

