package com.kau4dev.BetRadar.domain.exception;

public class TelegramChatAlreadyExistsException extends DomainValidationException {
    public TelegramChatAlreadyExistsException(String message) {
        super(message);
    }
}
