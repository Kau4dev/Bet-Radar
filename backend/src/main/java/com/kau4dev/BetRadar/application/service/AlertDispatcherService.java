package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.stereotype.Service;


import java.time.Instant;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertDispatcherService {

    private final AlertRepository alertRepository;

    @CacheEvict(cacheNames = "opportunities", allEntries = true)
    public void dispatchOpportunity(String matchId, AlertType type, String desc, Double margin) {
        validateDispatchInput(matchId, type, margin);

        Alert alert = new Alert(
                null,
                matchId,
                type,
                desc,
                margin,
                Instant.now()
        );
        alertRepository.save(alert);

        log.info("ALERTA ENVIADO: [{}] {} - Margem: {}%", type, desc, String.format("%.2f", margin));
    }

    private void validateDispatchInput(String matchId, AlertType type, Double margin) {
        if (matchId == null || matchId.isBlank()) {
            throw new DomainValidationException("matchId e obrigatorio para criar alerta");
        }

        if (type == null) {
            throw new DomainValidationException("type e obrigatorio para criar alerta");
        }

        if (margin == null || margin <= 0.0) {
            throw new DomainValidationException("margin deve ser maior que 0");
        }
    }
}