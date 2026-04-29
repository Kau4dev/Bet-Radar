package com.kau4dev.BetRadar.presentation.controller;

import com.kau4dev.BetRadar.application.service.TelegramChatService;
import com.kau4dev.BetRadar.domain.model.TelegramChat;
import com.kau4dev.BetRadar.presentation.mapper.TelegramChatResponseMapper;
import com.kau4dev.BetRadar.presentation.request.RegisterTelegramChatRequest;
import com.kau4dev.BetRadar.presentation.response.TelegramChatResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/notifications/telegram/chats")
@RequiredArgsConstructor
@Tag(name = "Telegram Notifications", description = "Gerenciamento de destinos Telegram para alertas (ADMIN only)")
public class TelegramChatController {

    private final TelegramChatService telegramChatService;
    private final TelegramChatResponseMapper mapper;

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Cadastrar chatId", description = "Adiciona um novo destino Telegram (usuario, grupo ou canal)")
    public ResponseEntity<TelegramChatResponse> registerChat(
            @Valid @RequestBody RegisterTelegramChatRequest request) {
        TelegramChat chat = telegramChatService.registerChat(request.chatId(), request.label());
        return ResponseEntity.status(201).body(mapper.toResponse(chat));
    }

    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Listar chatIds", description = "Retorna todos os destinos Telegram cadastrados")
    public ResponseEntity<List<TelegramChatResponse>> listChats() {
        List<TelegramChat> chats = telegramChatService.listChats();
        return ResponseEntity.ok(mapper.toResponseList(chats));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Remover chatId", description = "Remove um destino Telegram pelo ID interno")
    public ResponseEntity<Void> deleteChat(@PathVariable UUID id) {
        telegramChatService.deleteChat(id);
        return ResponseEntity.noContent().build();
    }
}
