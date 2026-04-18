package com.kau4dev.BetRadar.infrastructure.persistence.repository;

import com.kau4dev.BetRadar.infrastructure.entity.OddHistoryEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

public interface OddHistoryJpaRepository extends JpaRepository<OddHistoryEntity, UUID> {

    @Query(value = """
    SELECT DISTINCT ON (bookmaker_id) * FROM odd_history
    WHERE match_id = :matchId 
    ORDER BY bookmaker_id, timestamp DESC
    """, nativeQuery = true)
    List<OddHistoryEntity> findLatestOddsForEachBookmaker(String matchId);

}

