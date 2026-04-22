package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.port.NotificationSender;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertDispatcherService {

    @Value("${telegram.default-chat-id:}")
    private String defaultChatId;

    private final AlertRepository alertRepository;
    private final NotificationSender notificationSender;

    @CacheEvict(cacheNames = "opportunities", allEntries = true)
    public void dispatchOpportunity(String matchId, AlertType type, String desc, Double margin) {
        validateDispatchInput(matchId, type, margin);

        Alert alert = new Alert(
                null,
                matchId,
                type,
                desc,
                margin,
                Instant.now()
        );
        alertRepository.save(alert);

        String message = formatMessage(type, desc, margin);
        try {
            notificationSender.send(defaultChatId, message);
        } catch (Exception ex) {
            log.error("Falha ao enviar notificacao Telegram para alerta [{}]: {}", type, ex.getMessage());
        }

        log.info("ALERTA ENVIADO: [{}] {} - Margem: {}%", type, desc, String.format("%.2f", margin));
    }

    private String formatMessage(AlertType type, String desc, Double margin) {
        return String.format("[%s] %s - Margem: %.2f%%", type, desc, margin);
    }

    private void validateDispatchInput(String matchId, AlertType type, Double margin) {
        if (matchId == null || matchId.isBlank()) {
            throw new DomainValidationException("matchId e obrigatorio para criar alerta");
        }

        if (type == null) {
            throw new DomainValidationException("type e obrigatorio para criar alerta");
        }

        if (margin == null || margin <= 0.0) {
            throw new DomainValidationException("margin deve ser maior que 0");
        }
    }
}