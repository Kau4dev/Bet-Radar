package com.kau4dev.BetRadar.domain.port;

public interface NotificationSender {
    void send(String destination, String message);
}