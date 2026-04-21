package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.AlertValidationException;
import com.kau4dev.BetRadar.domain.exception.MatchNotFoundException;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Service
@RequiredArgsConstructor
public class AlertCommandService {

    private final AlertRepository alertRepository;
    private final MatchRepository matchRepository;

    public Alert createAlert(String matchId, String type, String description, Double profitMargin) {
        validateMatchExists(matchId);

        AlertType alertType = AlertType.fromValue(type);
        validateProfitMargin(profitMargin);

        Alert alertToSave = new Alert(
                null,
                matchId,
                alertType,
                description,
                profitMargin,
                Instant.now()
        );

        return alertRepository.save(alertToSave);
    }

    private void validateMatchExists(String matchId) {
        if (matchRepository.findById(matchId).isEmpty()) {
            throw new MatchNotFoundException("Partida nao encontrada para id: " + matchId);
        }
    }

    private void validateProfitMargin(Double profitMargin) {
        if (profitMargin == null || profitMargin <= 0.0) {
            throw new AlertValidationException("profitMargin deve ser maior que 0");
        }
    }
}
