package com.kau4dev.BetRadar.infrastructure.config.telegram;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Configuration
@EnableConfigurationProperties(TelegramProperties.class)
public class TelegramConfig {

    @Bean
    public RestClient telegramRestClient(TelegramProperties props) {
        return RestClient.builder()
                .defaultHeader("Accept", "application/json")
                .build();
    }
}
