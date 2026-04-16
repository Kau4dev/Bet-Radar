package com.kau4dev.BetRadar.infrastructure.messaging;

import com.kau4dev.BetRadar.application.dto.RawOddDTO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class RawOddsKafkaConsumer {

    @KafkaListener(topics = "raw-odds", groupId = "betradar-analytics-group")
    public void consumeRawOdds(RawOddDTO rawOddMessage) {

        log.info("🚀 Odd Recebida no Spring!");
        log.info("Casa: {}", rawOddMessage.bookmaker());
        log.info("Jogo: {} vs {}", rawOddMessage.teamHome(), rawOddMessage.teamAway());
        log.info("Odd Vitória Casa: {}", rawOddMessage.odds().homeWin());
        log.info("---------------------------------------------------");
    }
}