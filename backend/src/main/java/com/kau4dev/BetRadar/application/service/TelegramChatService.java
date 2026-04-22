package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.TelegramChatAlreadyExistsException;
import com.kau4dev.BetRadar.domain.exception.TelegramChatNotFoundException;
import com.kau4dev.BetRadar.domain.model.TelegramChat;
import com.kau4dev.BetRadar.domain.repository.TelegramChatRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class TelegramChatService {

    private final TelegramChatRepository telegramChatRepository;

    public TelegramChat registerChat(String chatId, String label) {
        validateChatId(chatId);

        if (telegramChatRepository.existsByChatId(chatId)) {
            throw new TelegramChatAlreadyExistsException("chatId ja cadastrado: " + chatId);
        }

        TelegramChat chat = new TelegramChat(null, chatId, label, Instant.now());
        TelegramChat saved = telegramChatRepository.save(chat);
        log.info("Telegram: chatId cadastrado id={} chatId={}", saved.id(), saved.chatId());
        return saved;
    }

    public List<TelegramChat> listChats() {
        return telegramChatRepository.findAll();
    }

    public void deleteChat(UUID id) {
        telegramChatRepository.findById(id)
                .orElseThrow(() -> new TelegramChatNotFoundException("Chat nao encontrado para id: " + id));
        telegramChatRepository.deleteById(id);
        log.info("Telegram: chatId removido id={}", id);
    }

    private void validateChatId(String chatId) {
        if (chatId == null || chatId.isBlank()) {
            throw new TelegramChatAlreadyExistsException("chatId e obrigatorio");
        }
        // Permite numerico positivo (usuario/grupo) e negativo (grupo/canal)
        if (!chatId.matches("^-?\\d+$")) {
            throw new TelegramChatAlreadyExistsException(
                    "chatId invalido. Deve ser numerico (ex: 123456789 ou -1001234567890)");
        }
    }
}
