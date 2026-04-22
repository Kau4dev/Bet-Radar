package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class AlertDispatcherServiceTest {

    @Mock
    AlertRepository alertRepository;

    private AlertDispatcherService service;

    @BeforeEach
    void setUp() {
        service = new AlertDispatcherService(alertRepository);
    }

    @Nested
    class DispatchOpportunity {

        @Test
        @DisplayName("Deve enviar alerta com sucesso")
        void deveEnviarAlertaComSucesso() {
            doReturn(new Alert(UUID.randomUUID(), "m1", AlertType.SUREBET, "Arb", 3.5, Instant.now()))
                    .when(alertRepository).save(any(Alert.class));

            service.dispatchOpportunity("m1", AlertType.SUREBET, "Arb", 3.5);

            ArgumentCaptor<Alert> captor = ArgumentCaptor.forClass(Alert.class);
            verify(alertRepository).save(captor.capture());
            assertEquals("m1", captor.getValue().matchId());
            assertEquals(AlertType.SUREBET, captor.getValue().type());
            assertEquals(3.5, captor.getValue().profitMargin());
        }

        @Test
        @DisplayName("Deve lancar excecao para matchId invalido")
        void deveLancarExcecaoParaMatchIdInvalido() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.dispatchOpportunity("  ", AlertType.EV_PLUS, "desc", 2.0));
            assertEquals("matchId e obrigatorio para criar alerta", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao para type nulo")
        void deveLancarExcecaoParaTypeNulo() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.dispatchOpportunity("m1", null, "desc", 2.0));
            assertEquals("type e obrigatorio para criar alerta", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao para margem invalida")
        void deveLancarExcecaoParaMargemInvalida() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.dispatchOpportunity("m1", AlertType.EV_PLUS, "desc", 0.0));
            assertEquals("margin deve ser maior que 0", ex.getMessage());
        }
    }
}

