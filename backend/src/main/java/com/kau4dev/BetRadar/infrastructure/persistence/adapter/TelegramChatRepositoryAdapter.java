package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.TelegramChat;
import com.kau4dev.BetRadar.domain.repository.TelegramChatRepository;
import com.kau4dev.BetRadar.infrastructure.entity.TelegramChatEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.mapper.TelegramChatPersistenceMapper;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.TelegramChatJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class TelegramChatRepositoryAdapter implements TelegramChatRepository {

    private final TelegramChatJpaRepository jpaRepository;
    private final TelegramChatPersistenceMapper mapper;

    @Override
    public TelegramChat save(TelegramChat telegramChat) {
        TelegramChatEntity entity = mapper.toEntity(telegramChat);
        return mapper.toDomain(jpaRepository.save(entity));
    }

    @Override
    public List<TelegramChat> findAll() {
        return mapper.toDomainList(jpaRepository.findAll());
    }

    @Override
    public Optional<TelegramChat> findById(UUID id) {
        return jpaRepository.findById(id).map(mapper::toDomain);
    }

    @Override
    public boolean existsByChatId(String chatId) {
        return jpaRepository.existsByChatId(chatId);
    }

    @Override
    public void deleteById(UUID id) {
        jpaRepository.deleteById(id);
    }
}
