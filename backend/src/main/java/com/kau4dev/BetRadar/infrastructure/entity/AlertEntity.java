package com.kau4dev.BetRadar.infrastructure.entity;


import com.kau4dev.BetRadar.infrastructure.entity.enums.AlertType;
import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "alerts")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class AlertEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "match_id", nullable = false)
    private String matchId;

    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private AlertType type;

    private String description;

    @Column(name = "profit_margin" , nullable = false)
    private Double profitMargin;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
}