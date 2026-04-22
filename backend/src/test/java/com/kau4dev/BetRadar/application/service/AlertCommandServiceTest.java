package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.AlertValidationException;
import com.kau4dev.BetRadar.domain.exception.MatchNotFoundException;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class AlertCommandServiceTest {

    @Mock
    AlertRepository alertRepository;
    @Mock
    MatchRepository matchRepository;

    private AlertCommandService service;

    @BeforeEach
    void setUp() {
        service = new AlertCommandService(alertRepository, matchRepository);
    }

    @Nested
    class CreateAlert {

        @Test
        @DisplayName("Deve criar alerta com sucesso")
        void deveCriarAlertaComSucesso() {
            doReturn(Optional.of(new Match("m1", "Real Madrid", "Barcelona"))).when(matchRepository).findById("m1");
            doReturn(new Alert(UUID.randomUUID(), "m1", AlertType.EV_PLUS, "desc", 5.0, Instant.now()))
                    .when(alertRepository).save(any(Alert.class));

            Alert created = service.createAlert("m1", "ev_plus", "desc", 5.0);

            assertEquals(AlertType.EV_PLUS, created.type());
            verify(alertRepository).save(any(Alert.class));

            ArgumentCaptor<Alert> captor = ArgumentCaptor.forClass(Alert.class);
            verify(alertRepository).save(captor.capture());
            assertEquals("m1", captor.getValue().matchId());
            assertEquals(AlertType.EV_PLUS, captor.getValue().type());
            assertEquals(5.0, captor.getValue().profitMargin());
        }

        @Test
        @DisplayName("Deve lancar excecao quando partida nao existe")
        void deveLancarExcecaoQuandoPartidaNaoExiste() {
            doReturn(Optional.empty()).when(matchRepository).findById("m1");

            MatchNotFoundException ex = assertThrows(MatchNotFoundException.class,
                    () -> service.createAlert("m1", "EV_PLUS", "desc", 5.0));

            assertEquals("Partida nao encontrada para id: m1", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao para tipo invalido")
        void deveLancarExcecaoParaTipoInvalido() {
            doReturn(Optional.of(new Match("m1", "A", "B"))).when(matchRepository).findById("m1");

            AlertValidationException ex = assertThrows(AlertValidationException.class,
                    () -> service.createAlert("m1", "invalid", "desc", 5.0));

            assertEquals("type invalido. Use EV_PLUS ou SUREBET", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao para margem nula")
        void deveLancarExcecaoParaMargemNula() {
            doReturn(Optional.of(new Match("m1", "A", "B"))).when(matchRepository).findById("m1");

            AlertValidationException ex = assertThrows(AlertValidationException.class,
                    () -> service.createAlert("m1", "EV_PLUS", "desc", null));

            assertEquals("profitMargin deve ser maior que 0", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao para margem menor ou igual a zero")
        void deveLancarExcecaoParaMargemMenorOuIgualAZero() {
            doReturn(Optional.of(new Match("m1", "A", "B"))).when(matchRepository).findById("m1");

            AlertValidationException ex = assertThrows(AlertValidationException.class,
                    () -> service.createAlert("m1", "EV_PLUS", "desc", 0.0));

            assertEquals("profitMargin deve ser maior que 0", ex.getMessage());
        }
    }
}

