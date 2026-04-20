package com.kau4dev.BetRadar.presentation.response;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;

import java.time.Instant;
import java.util.UUID;

public record OddHistoryResponse(
        UUID id,
        Double homeWinOdd,
        Double drawOdd,
        Double awayWinOdd,
        Instant timestamp,
        Match match,
        Bookmaker bookmaker
) {
}
