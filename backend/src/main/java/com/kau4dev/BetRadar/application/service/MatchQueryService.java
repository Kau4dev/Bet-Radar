package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Service
@RequiredArgsConstructor
public class MatchQueryService {

    private final MatchRepository matchRepository;
    private final OddHistoryRepository oddHistoryRepository;

    public List<Match> getActiveMatchesWithOdds() {
        return matchRepository.findAll();
    }

    public List<OddHistory> getOddTimeline(String matchId, int hoursBack) {
        Instant startTime = Instant.now().minus(hoursBack, ChronoUnit.HOURS);

        return oddHistoryRepository.findAll().stream()
                .filter(o -> o.match().id().equals(matchId))
                .filter(o -> o.timestamp().isAfter(startTime))
                .toList();
    }
}