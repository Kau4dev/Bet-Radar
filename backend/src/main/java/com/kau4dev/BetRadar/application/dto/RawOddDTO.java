package com.kau4dev.BetRadar.application.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;

public record RawOddDTO(
        String bookmaker,

        @JsonProperty("match_id")
        String matchId,

        @JsonProperty("team_home")
        String teamHome,

        @JsonProperty("team_away")
        String teamAway,

        OddsDTO odds,
        Instant timestamp
) {
    public record OddsDTO(
            @JsonProperty("home_win")
            Double homeWin,

            Double draw,

            @JsonProperty("away_win")
            Double awayWin
    ) {}
}