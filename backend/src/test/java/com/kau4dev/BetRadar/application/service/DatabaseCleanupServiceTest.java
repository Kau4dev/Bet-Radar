package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class DatabaseCleanupServiceTest {

    @Mock
    OddHistoryRepository oddHistoryRepository;

    private DatabaseCleanupService service;

    @BeforeEach
    void setUp() {
        service = new DatabaseCleanupService(oddHistoryRepository);
        ReflectionTestUtils.setField(service, "retentionHours", 48L);
    }

    @Nested
    class CleanupOldData {

        @Test
        @DisplayName("Deve executar limpeza e delegar para repository")
        void deveExecutarLimpezaEDelegarParaRepository() {
            doReturn(10L).when(oddHistoryRepository).deleteByTimestampBefore(any(Instant.class));

            Instant before = Instant.now();
            service.cleanupOldData();
            Instant after = Instant.now();

            ArgumentCaptor<Instant> captor = ArgumentCaptor.forClass(Instant.class);
            verify(oddHistoryRepository).deleteByTimestampBefore(captor.capture());

            Instant threshold = captor.getValue();
            assertTrue(threshold.isAfter(before.minusSeconds(48 * 3600 + 2)));
            assertTrue(threshold.isBefore(after.minusSeconds(48 * 3600 - 2)));
        }

        @Test
        @DisplayName("Deve engolir excecao de limpeza sem propagar")
        void deveEngolirExcecaoDeLimpezaSemPropagar() {
            doThrow(new RuntimeException("falhou")).when(oddHistoryRepository).deleteByTimestampBefore(any(Instant.class));

            service.cleanupOldData();

            verify(oddHistoryRepository).deleteByTimestampBefore(any(Instant.class));
        }
    }
}

