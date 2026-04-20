package com.kau4dev.BetRadar.presentation.controller;

import com.kau4dev.BetRadar.application.service.AlertCommandService;
import com.kau4dev.BetRadar.application.service.AlertQueryService;
import com.kau4dev.BetRadar.application.service.MatchQueryService;
import com.kau4dev.BetRadar.presentation.response.AlertResponse;
import com.kau4dev.BetRadar.presentation.response.CreateAlertRequest;
import com.kau4dev.BetRadar.presentation.response.MatchResponse;
import com.kau4dev.BetRadar.presentation.response.OddHistoryResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class BetRadarController {

    private final MatchQueryService matchQueryService;
    private final AlertCommandService alertCommandService;
    private final AlertQueryService alertQueryService;

    @PostMapping("/alerts")
    public ResponseEntity<AlertResponse> createAlert(@Valid @RequestBody CreateAlertRequest request) {
        AlertResponse alertRequest = alertCommandService.createAlert(request);
        return ResponseEntity.status(201).body(alertRequest);
    }

    @GetMapping("/opportunities")
    public ResponseEntity<List<AlertResponse>> getRecentOpportunities() {
        List<AlertResponse> alertResponse = alertQueryService.getRecentOpportunities();
        return ResponseEntity.status(200).body(alertResponse);
    }

    @GetMapping("/matches")
    public ResponseEntity<List<MatchResponse>> getMatches() {
        List<MatchResponse> matchResponse = matchQueryService.getActiveMatchesWithOdds();
        return ResponseEntity.status(200).body(matchResponse);
    }

    @GetMapping("/matches/{id}/timeline")
    public ResponseEntity<List<OddHistoryResponse>>getMatchHistory(
            @PathVariable String id,
            @RequestParam(defaultValue = "24") int hours)
    {
        List<OddHistoryResponse> oddHistoryResponses= matchQueryService.getOddTimeline(id, hours);
        return ResponseEntity.status(200).body(oddHistoryResponses);
    }

}