package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.MatchJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class MatchRepositoryAdapter implements MatchRepository {

    private final MatchJpaRepository jpaRepository;

    @Override
    public Optional<Match> findById(String id) {
        return jpaRepository.findById(id).map(this::toDomain);
    }

    @Override
    public List<Match> findAll() {
        return jpaRepository.findAll().stream().map(this::toDomain).toList();
    }

    @Override
    public Match save(Match match) {
        MatchEntity saved = jpaRepository.save(toEntity(match));
        return toDomain(saved);
    }

    private Match toDomain(MatchEntity entity) {
        return new Match(entity.getId(), entity.getTeamHome(), entity.getTeamAway());
    }

    private MatchEntity toEntity(Match domain) {
        return MatchEntity.builder()
                .id(domain.id())
                .teamHome(domain.teamHome())
                .teamAway(domain.teamAway())
                .build();
    }
}

