package com.kau4dev.BetRadar.presentation.response;

import java.time.Instant;
import java.util.UUID;

public record TelegramChatResponse(
        UUID id,
        String chatId,
        String label,
        Instant createdAt
) {}
