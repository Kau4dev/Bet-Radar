package com.kau4dev.BetRadar.domain.exception;

public class TelegramChatNotFoundException extends DomainValidationException {
    public TelegramChatNotFoundException(String message) {
        super(message);
    }
}
