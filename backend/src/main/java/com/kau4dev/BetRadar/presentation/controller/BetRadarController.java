package com.kau4dev.BetRadar.presentation.controller;

import com.kau4dev.BetRadar.application.service.AlertCommandService;
import com.kau4dev.BetRadar.application.service.AlertQueryService;
import com.kau4dev.BetRadar.application.service.MatchQueryService;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import lombok.RequiredArgsConstructor;
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
    public Alert createAlert(@RequestBody Alert alert) {
        return alertCommandService.createAlert(alert);
    }

    @GetMapping("/opportunities")
    public List<Alert> getRecentOpportunities() {
        return alertQueryService.getRecentOpportunities();
    }

    @GetMapping("/matches")
    public List<Match> getMatches() {
        return matchQueryService.getActiveMatchesWithOdds();
    }

    @GetMapping("/matches/{id}/timeline")
    public List<OddHistory> getMatchHistory(
            @PathVariable String id,
            @RequestParam(defaultValue = "24") int hours) {
        return matchQueryService.getOddTimeline(id, hours);
    }

}