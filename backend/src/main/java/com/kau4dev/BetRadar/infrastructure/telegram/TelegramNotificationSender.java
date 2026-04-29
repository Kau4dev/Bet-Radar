package com.kau4dev.BetRadar.infrastructure.telegram;

import com.kau4dev.BetRadar.domain.port.NotificationSender;
import com.kau4dev.BetRadar.infrastructure.config.telegram.TelegramProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

/**
 * Adapter de infraestrutura que implementa NotificationSender via API do Telegram.
 * Nunca propaga excecoes para nao derrubar o fluxo principal de alertas.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class TelegramNotificationSender implements NotificationSender {

    private final TelegramProperties props;
    private final RestClient telegramRestClient;

    @Override
    public void send(String destination, String message) {
        if (!props.enabled()) {
            log.debug("Telegram desabilitado — mensagem ignorada");
            return;
        }

        String chatId = (destination == null || destination.isBlank())
                ? props.defaultChatId()
                : destination;

        if (chatId == null || chatId.isBlank()) {
            log.warn("Telegram: chatId nao configurado — mensagem ignorada");
            return;
        }

        try {
            String url = props.baseUrl() + "/bot" + props.token() + "/sendMessage";
            String body = "chat_id=" + URLEncoder.encode(chatId, StandardCharsets.UTF_8)
                    + "&text=" + URLEncoder.encode(message, StandardCharsets.UTF_8);

            telegramRestClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                    .body(body)
                    .retrieve()
                    .toBodilessEntity();

            log.debug("Telegram: mensagem enviada para chatId={}", chatId);
        } catch (Exception ex) {
            log.error("Telegram: falha ao enviar mensagem para chatId={}: {}", chatId, ex.getMessage());
            // Nao propaga: o fluxo principal (Kafka/alertas) nao deve ser interrompido por falha de notificacao
        }
    }
}
