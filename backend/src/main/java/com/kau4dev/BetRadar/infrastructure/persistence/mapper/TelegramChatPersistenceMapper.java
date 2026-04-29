package com.kau4dev.BetRadar.infrastructure.persistence.mapper;

import com.kau4dev.BetRadar.domain.model.TelegramChat;
import com.kau4dev.BetRadar.infrastructure.entity.TelegramChatEntity;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface TelegramChatPersistenceMapper {

    TelegramChat toDomain(TelegramChatEntity entity);

    TelegramChatEntity toEntity(TelegramChat telegramChat);

    List<TelegramChat> toDomainList(List<TelegramChatEntity> entities);
}
