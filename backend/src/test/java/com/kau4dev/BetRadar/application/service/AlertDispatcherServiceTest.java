package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.port.NotificationSender;
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
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AlertDispatcherServiceTest {

    @Mock
    AlertRepository alertRepository;

    @Mock
    NotificationSender notificationSender;

    private AlertDispatcherService service;

    @BeforeEach
    void setUp() {
        service = new AlertDispatcherService(alertRepository, notificationSender);
    }

    @Nested
    class DispatchOpportunity {

        @Test
        @DisplayName("Deve salvar alerta e chamar notificationSender com sucesso")
        void deveSalvarAlertaEChamarNotificationSender() {
            doReturn(new Alert(UUID.randomUUID(), "m1", AlertType.SUREBET, "Arb", 3.5, Instant.now()))
                    .when(alertRepository).save(any(Alert.class));

            service.dispatchOpportunity("m1", AlertType.SUREBET, "Arb", 3.5);

            ArgumentCaptor<Alert> captor = ArgumentCaptor.forClass(Alert.class);
            verify(alertRepository).save(captor.capture());
            assertEquals("m1", captor.getValue().matchId());
            assertEquals(AlertType.SUREBET, captor.getValue().type());
            assertEquals(3.5, captor.getValue().profitMargin());

            verify(notificationSender).send(isNull(), contains("[SUREBET]"));
        }

        @Test
        @DisplayName("Nao deve propagar excecao se notificationSender falhar")
        void naoDevePropagarExcecaoSeNotificationSenderFalhar() {
            doReturn(new Alert(UUID.randomUUID(), "m1", AlertType.EV_PLUS, "desc", 2.0, Instant.now()))
                    .when(alertRepository).save(any(Alert.class));
            doThrow(new RuntimeException("Telegram indisponivel"))
                    .when(notificationSender).send(anyString(), anyString());

            // Nao deve lancar excecao — o fluxo principal nao pode ser interrompido
            service.dispatchOpportunity("m1", AlertType.EV_PLUS, "desc", 2.0);

            verify(alertRepository).save(any(Alert.class));
        }

        @Test
        @DisplayName("Deve lancar excecao para matchId invalido")
        void deveLancarExcecaoParaMatchIdInvalido() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.dispatchOpportunity("  ", AlertType.EV_PLUS, "desc", 2.0));
            assertEquals("matchId e obrigatorio para criar alerta", ex.getMessage());

            verifyNoInteractions(notificationSender);
        }

        @Test
        @DisplayName("Deve lancar excecao para type nulo")
        void deveLancarExcecaoParaTypeNulo() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.dispatchOpportunity("m1", null, "desc", 2.0));
            assertEquals("type e obrigatorio para criar alerta", ex.getMessage());

            verifyNoInteractions(notificationSender);
        }

        @Test
        @DisplayName("Deve lancar excecao para margem invalida")
        void deveLancarExcecaoParaMargemInvalida() {
            DomainValidationException ex = assertThrows(DomainValidationException.class,
                    () -> service.dispatchOpportunity("m1", AlertType.EV_PLUS, "desc", 0.0));
            assertEquals("margin deve ser maior que 0", ex.getMessage());

            verifyNoInteractions(notificationSender);
        }
    }
}
