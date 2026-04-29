package com.kau4dev.BetRadar.domain.model;

import java.time.Instant;
import java.util.UUID;

public record TelegramChat(
        UUID id,
        String chatId,
        String label,
        Instant createdAt
) {}
