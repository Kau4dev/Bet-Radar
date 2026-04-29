package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.OddHistory;

import java.time.Instant;
import java.util.List;

public interface OddHistoryRepository {

    List<OddHistory> findLatestOddsForEachBookmaker(String matchId);

    List<OddHistory> findAll();

    OddHistory save(OddHistory oddHistory);

    long deleteByTimestampBefore(Instant threshold);


}
