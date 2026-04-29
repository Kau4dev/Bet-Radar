package com.kau4dev.BetRadar.infrastructure.config.telegram;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "telegram")
public record TelegramProperties(
        boolean enabled,
        Bot bot,
        String defaultChatId,
        int connectTimeoutMs,
        int readTimeoutMs,
        int maxRetries
) {
    public String token()   { return bot.token(); }
    public String baseUrl() { return bot.baseUrl(); }

    public record Bot(String token, String baseUrl) {}
}
