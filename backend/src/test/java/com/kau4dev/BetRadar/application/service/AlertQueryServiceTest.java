package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.doReturn;

@ExtendWith(MockitoExtension.class)
class AlertQueryServiceTest {

    @Mock
    AlertRepository alertRepository;

    private AlertQueryService service;

    @BeforeEach
    void setUp() {
        service = new AlertQueryService(alertRepository);
    }

    @Test
    @DisplayName("Deve retornar apenas oportunidades recentes")
    void deveRetornarApenasOportunidadesRecentes() {
        Alert recent = new Alert(UUID.randomUUID(), "m1", AlertType.EV_PLUS, "desc", 4.0, Instant.now().minusSeconds(300));
        Alert old = new Alert(UUID.randomUUID(), "m1", AlertType.SUREBET, "old", 2.0, Instant.now().minusSeconds(4000));

        doReturn(List.of(recent, old)).when(alertRepository).findAll();

        List<Alert> result = service.getRecentOpportunities();

        assertEquals(1, result.size());
        assertEquals(recent.id(), result.getFirst().id());
    }
}

