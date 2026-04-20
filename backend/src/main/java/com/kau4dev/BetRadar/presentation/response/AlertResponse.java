package com.kau4dev.BetRadar.presentation.response;

import java.time.Instant;
import java.util.UUID;

public record AlertResponse(
        UUID id,
        String matchId,
        String type,
        String description,
        Double profitMargin,
        Instant createdAt) {
}
