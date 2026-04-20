package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import com.kau4dev.BetRadar.infrastructure.entity.OddHistoryEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.mapper.OddHistoryPersistenceMapper;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.OddHistoryJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class OddHistoryRepositoryAdapter implements OddHistoryRepository {

    private final OddHistoryJpaRepository jpaRepository;
    private final OddHistoryPersistenceMapper mapper;


    @Override
    public List<OddHistory> findLatestOddsForEachBookmaker(String matchId) {
        return jpaRepository.findLatestOddsForEachBookmaker(matchId)
                .stream()
                .map(mapper::toDomain)
                .toList();
    }

    // puxar com querry dps
    @Override
    public List<OddHistory> findAll() {
        return mapper.toDomainList(jpaRepository.findAll());
    }

    @Override
    public OddHistory save(OddHistory oddHistory) {
        OddHistoryEntity entity = mapper.toEntity(oddHistory);
        OddHistoryEntity savedEntity = jpaRepository.save(entity);
        return mapper.toDomain(savedEntity);
    }

}

