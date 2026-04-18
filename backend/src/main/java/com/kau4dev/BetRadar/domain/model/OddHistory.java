package com.kau4dev.BetRadar.domain.model;

import java.time.Instant;
import java.util.UUID;

public record OddHistory(
        UUID id,
        Double homeWinOdd,
        Double drawOdd,
        Double awayWinOdd,
        Instant timestamp,
        Match match,
        Bookmaker bookmaker
) {
}

