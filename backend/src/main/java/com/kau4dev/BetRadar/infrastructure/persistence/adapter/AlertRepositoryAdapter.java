package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import com.kau4dev.BetRadar.infrastructure.entity.AlertEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.AlertJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class AlertRepositoryAdapter implements AlertRepository {

    private final AlertJpaRepository jpaRepository;

    @Override
    public Alert save(Alert alert) {
        AlertEntity saved = jpaRepository.save(toEntity(alert));
        return toDomain(saved);
    }

    private Alert toDomain(AlertEntity entity) {
        return new Alert(entity.getId(), entity.getMatchId(), entity.getType(), entity.getDescription(),
                entity.getProfitMargin(), entity.getCreatedAt());
    }

    private AlertEntity toEntity(Alert domain) {
        return AlertEntity.builder()
                .id(domain.id())
                .matchId(domain.matchId())
                .type(domain.type())
                .description(domain.description())
                .profitMargin(domain.profitMargin())
                .createdAt(domain.createdAt())
                .build();
    }
}
