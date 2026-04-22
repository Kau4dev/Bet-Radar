package com.kau4dev.BetRadar.presentation.controller;

import com.kau4dev.BetRadar.application.service.AlertCommandService;
import com.kau4dev.BetRadar.application.service.AlertQueryService;
import com.kau4dev.BetRadar.application.service.MatchQueryService;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.presentation.mapper.AlertResponseMapper;
import com.kau4dev.BetRadar.presentation.mapper.MatchResponseMapper;
import com.kau4dev.BetRadar.presentation.mapper.OddHistoryResponseMapper;
import com.kau4dev.BetRadar.presentation.response.AlertResponse;
import com.kau4dev.BetRadar.presentation.request.CreateAlertRequest;
import com.kau4dev.BetRadar.presentation.response.MatchResponse;
import com.kau4dev.BetRadar.presentation.response.OddHistoryResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class BetRadarController {

    private final MatchQueryService matchQueryService;
    private final AlertCommandService alertCommandService;
    private final AlertQueryService alertQueryService;
    private final MatchResponseMapper matchResponseMapper;
    private final AlertResponseMapper alertResponseMapper;
    private final OddHistoryResponseMapper oddHistoryResponseMapper;

    @PostMapping("/alerts")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<AlertResponse> createAlert(@Valid @RequestBody CreateAlertRequest request) {
        Alert alert = alertCommandService.createAlert(
                request.matchId(),
                request.type(),
                request.description(),
                request.profitMargin()
        );
        AlertResponse alertRequest = alertResponseMapper.toAlertResponse(alert);
        return ResponseEntity.status(201).body(alertRequest);
    }

    @GetMapping("/opportunities")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<AlertResponse>> getRecentOpportunities() {
        List<Alert> alerts = alertQueryService.getRecentOpportunities();
        List<AlertResponse> alertResponse = alertResponseMapper.toAlertResponseList(alerts);
        return ResponseEntity.status(200).body(alertResponse);
    }

    @GetMapping("/matches")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<MatchResponse>> getMatches() {
        List<Match> matches = matchQueryService.getActiveMatchesWithOdds();
        List<MatchResponse> matchResponse = matchResponseMapper.toMatchResponseList(matches);
        return ResponseEntity.status(200).body(matchResponse);
    }

    @GetMapping("/matches/{id}/timeline")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<OddHistoryResponse>>getMatchHistory(
            @PathVariable String id,
            @RequestParam(defaultValue = "24") int hours)
    {
        List<OddHistory> oddHistories = matchQueryService.getOddTimeline(id, hours);
        List<OddHistoryResponse> oddHistoryResponses = oddHistoryResponseMapper.toOddHistoryResponseList(oddHistories);
        return ResponseEntity.status(200).body(oddHistoryResponses);
    }

}