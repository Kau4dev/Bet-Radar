package com.kau4dev.BetRadar.presentation.mapper;

import com.kau4dev.BetRadar.domain.model.TelegramChat;
import com.kau4dev.BetRadar.presentation.response.TelegramChatResponse;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface TelegramChatResponseMapper {

    TelegramChatResponse toResponse(TelegramChat telegramChat);

    List<TelegramChatResponse> toResponseList(List<TelegramChat> chats);
}
