package com.kau4dev.BetRadar.infrastructure.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.*;

@Entity
@Table(name = "matches")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class MatchEntity {

    @Id
    private String id;

    @Column(name = "team_home", nullable = false)
    private String teamHome;

    @Column(name = "team_away", nullable = false)
    private String teamAway;
}
