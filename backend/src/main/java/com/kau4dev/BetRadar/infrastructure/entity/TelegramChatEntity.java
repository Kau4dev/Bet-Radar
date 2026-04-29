package com.kau4dev.BetRadar.infrastructure.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(
        name = "telegram_chats",
        uniqueConstraints = @UniqueConstraint(name = "uk_telegram_chats_chat_id", columnNames = "chat_id")
)
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class TelegramChatEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "chat_id", nullable = false)
    private String chatId;

    @Column(name = "label")
    private String label;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
}
