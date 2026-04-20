package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import com.kau4dev.BetRadar.presentation.mapper.AlertResponseMapper;
import com.kau4dev.BetRadar.presentation.response.AlertResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AlertQueryService {

    private final AlertRepository alertRepository;
    private final AlertResponseMapper alertResponseMapper;


    public List<AlertResponse> getRecentOpportunities () {
        return alertResponseMapper.toAlertResponseList(alertRepository.findAll()).stream()
                .filter(alert -> alert.createdAt().isAfter(Instant.now().minusSeconds(3600)))
                .toList();
    }

}
