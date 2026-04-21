package com.kau4dev.BetRadar.domain.model;

import com.kau4dev.BetRadar.domain.model.enums.UserRole;

import java.util.UUID;

public record User(
        UUID id,
        String username,
        String passwordHash,
        UserRole role,
        boolean enabled
) {
}
