package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.domain.exception.MatchNotFoundException;
import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.doReturn;

@ExtendWith(MockitoExtension.class)
class MatchQueryServiceTest {

    @Mock
    MatchRepository matchRepository;
    @Mock
    OddHistoryRepository oddHistoryRepository;

    private MatchQueryService service;

    @BeforeEach
    void setUp() {
        service = new MatchQueryService(matchRepository, oddHistoryRepository);
    }

    @Test
    @DisplayName("Deve retornar partidas ativas")
    void deveRetornarPartidasAtivas() {
        List<Match> matches = List.of(new Match("m1", "A", "B"));
        doReturn(matches).when(matchRepository).findAll();

        List<Match> result = service.getActiveMatchesWithOdds();

        assertEquals(1, result.size());
        assertEquals("m1", result.getFirst().id());
    }

    @Nested
    class GetOddTimeline {

        @Test
        @DisplayName("Deve retornar timeline filtrada por partida e janela")
        void deveRetornarTimelineFiltradaPorPartidaEJanela() {
            Match match = new Match("m1", "A", "B");
            doReturn(Optional.of(match)).when(matchRepository).findById("m1");

            OddHistory inWindow = new OddHistory(UUID.randomUUID(), 2.1, 3.2, 3.4,
                    Instant.now().minusSeconds(1800), match, new Bookmaker(UUID.randomUUID(), "Betano"));
            OddHistory outWindow = new OddHistory(UUID.randomUUID(), 2.1, 3.2, 3.4,
                    Instant.now().minusSeconds(5 * 3600), match, new Bookmaker(UUID.randomUUID(), "Pinnacle"));
            OddHistory otherMatch = new OddHistory(UUID.randomUUID(), 2.1, 3.2, 3.4,
                    Instant.now().minusSeconds(1800), new Match("m2", "C", "D"), new Bookmaker(UUID.randomUUID(), "Bet365"));

            doReturn(List.of(inWindow, outWindow, otherMatch)).when(oddHistoryRepository).findAll();

            List<OddHistory> result = service.getOddTimeline("m1", 2);

            assertEquals(1, result.size());
            assertEquals(inWindow.id(), result.getFirst().id());
        }

        @Test
        @DisplayName("Deve lancar excecao para matchId vazio")
        void deveLancarExcecaoParaMatchIdVazio() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.getOddTimeline(" ", 1));
            assertEquals("matchId e obrigatorio", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao para hoursBack invalido")
        void deveLancarExcecaoParaHoursBackInvalido() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.getOddTimeline("m1", 0));
            assertEquals("hoursBack deve ser maior que 0", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao quando partida nao existe")
        void deveLancarExcecaoQuandoPartidaNaoExiste() {
            doReturn(Optional.empty()).when(matchRepository).findById("m1");

            MatchNotFoundException ex = assertThrows(MatchNotFoundException.class,
                    () -> service.getOddTimeline("m1", 1));

            assertEquals("Partida nao encontrada para id: m1", ex.getMessage());
        }
    }
}

