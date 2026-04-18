package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.Match;

import java.util.List;
import java.util.Optional;

public interface MatchRepository {

    Optional<Match> findById(String id);

    List<Match> findAll();

    Match save(Match match);

}
