package com.kau4dev.BetRadar.domain.exception;

public class NotNullTimeException extends DomainValidationException {
    public NotNullTimeException(String message) {
        super(message);
    }
}
