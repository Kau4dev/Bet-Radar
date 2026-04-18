package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.OddHistory;

import java.util.List;

public interface OddHistoryRepository {

    List<OddHistory> findLatestOddsForEachBookmaker(String matchId);

    OddHistory save(OddHistory oddHistory);
}
