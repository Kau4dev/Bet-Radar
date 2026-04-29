package com.kau4dev.BetRadar.domain.exception;

public class UserAlreadyExistsException extends DomainValidationException {

    public UserAlreadyExistsException(String message) {
        super(message);
    }
}

