package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Service
@RequiredArgsConstructor
public class AlertCommandService {

    private final AlertRepository alertRepository;

    public Alert createAlert(Alert alert) {
        Alert alertToSave = new Alert(
                null, // deixa o banco gerar ID
                alert.matchId(),
                alert.type(),
                alert.description(),
                alert.profitMargin(),
                alert.createdAt() != null ? alert.createdAt() : Instant.now()
        );
        return alertRepository.save(alertToSave);
    }

}
