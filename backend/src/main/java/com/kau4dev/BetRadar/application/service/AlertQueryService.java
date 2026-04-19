package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AlertQueryService {

    private final AlertRepository alertRepository;


    public List<Alert> getRecentOpportunities () {
        return alertRepository.findAll().stream()
                .filter(alert -> alert.createdAt().isAfter(Instant.now().minusSeconds(3600))) // Última hora
                .toList();
    }
}
