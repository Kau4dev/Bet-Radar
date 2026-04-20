package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import com.kau4dev.BetRadar.presentation.mapper.MatchResponseMapper;
import com.kau4dev.BetRadar.presentation.response.MatchResponse;
import com.kau4dev.BetRadar.presentation.response.OddHistoryResponse;
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
    private final MatchResponseMapper matchResponseMapper;

    public List<MatchResponse> getActiveMatchesWithOdds() {
        return matchResponseMapper.toMatchResponseList(matchRepository.findAll());
    }

    public List<OddHistoryResponse> getOddTimeline(String matchId, int hoursBack) {
        Instant startTime = Instant.now().minus(hoursBack, ChronoUnit.HOURS);

        return oddHistoryRepository.findAll().stream()
                .filter(o -> o.match().id().equals(matchId))
                .filter(o -> o.timestamp().isAfter(startTime))
                .map(matchResponseMapper::toOddHistoryResponse)
                .toList();
    }
}