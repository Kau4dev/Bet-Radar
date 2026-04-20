package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import com.kau4dev.BetRadar.presentation.mapper.AlertResponseMapper;
import com.kau4dev.BetRadar.presentation.response.AlertResponse;
import com.kau4dev.BetRadar.presentation.response.CreateAlertRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Service
@RequiredArgsConstructor
public class AlertCommandService {

    private final AlertRepository alertRepository;
    private final AlertResponseMapper alertResponseMapper;

    public AlertResponse createAlert(CreateAlertRequest request) {
        Alert alertToSave = new Alert(
                null,
                request.matchId(),
                request.type(),
                request.description(),
                request.profitMargin(),
                Instant.now()
        );

        return alertResponseMapper.toAlertResponse(alertRepository.save(alertToSave));
    }

}
