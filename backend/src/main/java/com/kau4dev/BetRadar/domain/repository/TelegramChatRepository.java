package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.TelegramChat;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface TelegramChatRepository {

    TelegramChat save(TelegramChat telegramChat);

    List<TelegramChat> findAll();

    Optional<TelegramChat> findById(UUID id);

    boolean existsByChatId(String chatId);

    void deleteById(UUID id);
}
