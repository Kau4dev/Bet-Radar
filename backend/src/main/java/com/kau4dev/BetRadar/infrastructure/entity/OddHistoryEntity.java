package com.kau4dev.BetRadar.infrastructure.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "odd_history")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class OddHistoryEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "home_win_odd", nullable = false)
    private Double homeWinOdd;

    @Column(name = "draw_odd", nullable = false)
    private Double drawOdd;

    @Column(name = "away_win_odd", nullable = false)
    private Double awayWinOdd;

    @Column(nullable = false)
    private Instant timestamp;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "match_id", nullable = false)
    private MatchEntity match;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "bookmaker_id", nullable = false)
    private BookmakerEntity bookmaker;
}
