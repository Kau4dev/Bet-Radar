package com.kau4dev.BetRadar.domain.model;

import java.time.Instant;
import java.util.UUID;

public record Alert(
        UUID id,
        String matchId,
        String type,
        String description,
        Double profitMargin,
        Instant createdAt) {
}
