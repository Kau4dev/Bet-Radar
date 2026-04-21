package com.kau4dev.BetRadar.presentation.request;

import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @NotBlank(message = "username e obrigatorio")
        String username,
        @NotBlank(message = "password e obrigatorio")
        String password
) {
}

