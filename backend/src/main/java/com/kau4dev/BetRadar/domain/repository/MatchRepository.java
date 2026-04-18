package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.Match;

import java.util.Optional;

public interface MatchRepository {

    Optional<Match> findById(String id);

    Match save(Match match);
}
