package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;


import java.time.Instant;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertDispatcherService {

    private final AlertRepository alertRepository;

    public void dispatchOpportunity(String matchId, String type, String desc, Double margin) {

        Alert alert = new Alert(
                null,
                matchId,
                type,
                desc,
                margin,
                Instant.now()
        );
        alertRepository.save(alert);

        log.info("📢 ALERTA ENVIADO: [{}] {} - Margem: {}%", type, desc, String.format("%.2f", margin));
    }

}