package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.mapper.MatchPersistenceMapper;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.MatchJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class MatchRepositoryAdapter implements MatchRepository {

    private final MatchJpaRepository jpaRepository;
    private final MatchPersistenceMapper mapper;

    @Override
    public Optional<Match> findById(String id) {
        return jpaRepository.findById(id)
                .map(mapper::toDomain);
    }

    @Override
    public List<Match> findAll() {
        return mapper.toDomainList(jpaRepository.findAll());
    }

    @Override
    public Match save(Match match) {
        MatchEntity entity = mapper.toEntity(match);
        MatchEntity savedEntity = jpaRepository.save(entity);
        return mapper.toDomain(savedEntity);
    }

}

