package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.temporal.ChronoUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class DatabaseCleanupService {

    private final OddHistoryRepository oddHistoryRepository;

    @Value("${app.cleanup.odds-retention-hours:48}")
    private long retentionHours;

    @Scheduled(cron = "${app.cleanup.cron:0 0 3 * * *}")
    @Transactional
    public void cleanupOldData() {
        Instant threshold = Instant.now().minus(retentionHours, ChronoUnit.HOURS);

        try {
            long deleted = oddHistoryRepository.deleteByTimestampBefore(threshold);
            log.info("Limpeza concluida: {} registros de odd_history removidos (antes de {}).", deleted, threshold);
        } catch (Exception e) {
            log.error("Erro durante limpeza automatica de odd_history", e);
        }
    }
}

