package com.kau4dev.BetRadar.presentation.response;

import java.util.UUID;

public record CreateUserResponse(
        UUID id,
        String username,
        String role,
        boolean enabled
) {
}

