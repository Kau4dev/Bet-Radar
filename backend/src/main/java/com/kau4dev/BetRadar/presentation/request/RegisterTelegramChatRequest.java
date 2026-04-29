package com.kau4dev.BetRadar.presentation.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record RegisterTelegramChatRequest(

        @NotBlank(message = "chatId e obrigatorio")
        @Pattern(regexp = "^-?\\d+$", message = "chatId deve ser numerico (ex: 123456789 ou -1001234567890)")
        String chatId,

        String label
) {}
