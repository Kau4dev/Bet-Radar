package com.kau4dev.BetRadar.domain.model;

import com.kau4dev.BetRadar.domain.exception.AlertValidationException;

import java.util.Locale;

public enum AlertType {
    EV_PLUS,
    SUREBET;

    public static AlertType fromValue(String rawType) {
        if (rawType == null || rawType.isBlank()) {
            throw new AlertValidationException("type e obrigatorio");
        }

        try {
            return AlertType.valueOf(rawType.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException ex) {
            throw new AlertValidationException("type invalido. Use EV_PLUS ou SUREBET");
        }
    }
}

