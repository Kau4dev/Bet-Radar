package com.kau4dev.BetRadar.infrastructure.messaging;

import com.kau4dev.BetRadar.application.dto.RawOddDTO;
import com.kau4dev.BetRadar.application.service.OddProcessorService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class RawOddsKafkaConsumer {

    private final OddProcessorService oddProcessorService;

    @KafkaListener(topics = "raw-odds", groupId = "betradar-analytics-group")
    public void consumeRawOdds(RawOddDTO rawOddMessage) {

        try {
            oddProcessorService.processAndStore(rawOddMessage);
            log.info("Processado com sucesso: {} | {}", rawOddMessage.bookmaker(), rawOddMessage.matchId());
        } catch (Exception e) {
            log.error("Erro ao processar mensagem do Kafka: {}", e.getMessage());
        }

    }
}