package com.kau4dev.BetRadar.infrastructure.persistence.repository;

import com.kau4dev.BetRadar.infrastructure.entity.TelegramChatEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface TelegramChatJpaRepository extends JpaRepository<TelegramChatEntity, UUID> {

    boolean existsByChatId(String chatId);
}
