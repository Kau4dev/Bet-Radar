package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
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
import java.util.UUID;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class MarketAnalyzerServiceTest {

    @Mock
    OddHistoryRepository oddHistoryRepository;
    @Mock
    AlertDispatcherService alertDispatcherService;

    private MarketAnalyzerService service;

    @BeforeEach
    void setUp() {
        service = new MarketAnalyzerService(oddHistoryRepository, alertDispatcherService);
    }

    private OddHistory odd(String bookmaker, double home, double draw, double away) {
        return new OddHistory(
                UUID.randomUUID(),
                home,
                draw,
                away,
                Instant.now(),
                new Match("m1", "A", "B"),
                new Bookmaker(UUID.randomUUID(), bookmaker)
        );
    }

    @Nested
    class CalculateExpectedValue {

        @Test
        @DisplayName("Deve ignorar quando mercado tem menos de 2 casas")
        void deveIgnorarQuandoMercadoTemMenosDe2Casas() {
            doReturn(List.of(odd("Betano", 2.0, 3.0, 3.5)))
                    .when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.calculateExpectedValue("m1", "Pinnacle", 2.5, 3.2, 3.6, 0.05);

            verify(alertDispatcherService, never())
                    .dispatchOpportunity(eq("m1"), eq(AlertType.EV_PLUS), anyString(), anyDouble());
        }

        @Test
        @DisplayName("Deve disparar EV+ com bookmaker e outcome na descricao")
        void deveDispararEvComBookmakerEOutcomeNaDescricao() {
            doReturn(List.of(
                    odd("Betano", 2.0, 3.0, 3.0),
                    odd("Bet365", 2.0, 3.0, 3.0)
            )).when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.calculateExpectedValue("m1", "Pinnacle", 2.4, 3.0, 3.0, 0.05);

            verify(alertDispatcherService).dispatchOpportunity(
                    eq("m1"),
                    eq(AlertType.EV_PLUS),
                    // Mensagem deve conter o outcome e o nome do bookmaker
                    argThat(desc -> desc.contains("HOME") && desc.contains("Pinnacle")),
                    anyDouble()
            );
        }

        @Test
        @DisplayName("Deve ignorar odds invalidas e nao disparar")
        void deveIgnorarOddsInvalidasENaoDisparar() {
            doReturn(List.of(
                    odd("Betano", 2.0, 3.0, 3.0),
                    odd("Bet365", 2.0, 3.0, 3.0)
            )).when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.calculateExpectedValue("m1", "Pinnacle", null, 0.0, -1.0, 0.05);

            verify(alertDispatcherService, never())
                    .dispatchOpportunity(eq("m1"), eq(AlertType.EV_PLUS), anyString(), anyDouble());
        }

        @Test
        @DisplayName("Deve ignorar quando media de mercado for invalida")
        void deveIgnorarQuandoMediaDeMercadoForInvalida() {
            doReturn(List.of(
                    odd("Betano", 0.0, 0.0, 0.0),
                    odd("Bet365", 0.0, 0.0, 0.0)
            )).when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.calculateExpectedValue("m1", "Pinnacle", 2.5, 3.0, 3.0, 0.05);

            verify(alertDispatcherService, never())
                    .dispatchOpportunity(eq("m1"), eq(AlertType.EV_PLUS), anyString(), anyDouble());
        }
    }

    @Nested
    class DetectSurebet {

        @Test
        @DisplayName("Deve ignorar surebet com poucas casas")
        void deveIgnorarSurebetComPoucasCasas() {
            doReturn(List.of(odd("Betano", 2.0, 3.0, 3.0)))
                    .when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.detectSurebet("m1");

            verify(alertDispatcherService, never())
                    .dispatchOpportunity(eq("m1"), eq(AlertType.SUREBET), anyString(), anyDouble());
        }

        @Test
        @DisplayName("Deve disparar surebet com casas e percentuais na descricao")
        void deveDispararSurebetComCasasEPercentuaisNaDescricao() {
            doReturn(List.of(
                    odd("Betano", 2.4, 3.6, 4.2),
                    odd("Bet365", 2.5, 3.7, 4.3)
            )).when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.detectSurebet("m1");

            verify(alertDispatcherService).dispatchOpportunity(
                    eq("m1"),
                    eq(AlertType.SUREBET),
                    // Mensagem deve conter as casas e os percentuais
                    argThat(desc ->
                            desc.contains("Casa:") &&
                            desc.contains("Empate:") &&
                            desc.contains("Fora:") &&
                            desc.contains("%")
                    ),
                    anyDouble()
            );
        }

        @Test
        @DisplayName("Nao deve disparar quando indice de arbitragem for >= 1")
        void naoDeveDispararQuandoIndiceForMaiorOuIgualUm() {
            doReturn(List.of(
                    odd("Betano", 1.8, 2.8, 3.0),
                    odd("Bet365", 1.9, 2.9, 3.1)
            )).when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.detectSurebet("m1");

            verify(alertDispatcherService, never())
                    .dispatchOpportunity(eq("m1"), eq(AlertType.SUREBET), anyString(), anyDouble());
        }

        @Test
        @DisplayName("Nao deve disparar quando alguma odd maxima for zero")
        void naoDeveDispararQuandoAlgumaOddMaximaForZero() {
            doReturn(List.of(
                    odd("Betano", 2.2, 0.0, 3.2),
                    odd("Bet365", 2.1, 0.0, 3.1)
            )).when(oddHistoryRepository).findLatestOddsForEachBookmaker("m1");

            service.detectSurebet("m1");

            verify(alertDispatcherService, never())
                    .dispatchOpportunity(eq("m1"), eq(AlertType.SUREBET), anyString(), anyDouble());
        }
    }
}
