package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.repository.AlertRepository;
import com.kau4dev.BetRadar.infrastructure.entity.AlertEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.mapper.AlertPersistenceMapper;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.AlertJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class AlertRepositoryAdapter implements AlertRepository {

    private final AlertJpaRepository jpaRepository;
    private final AlertPersistenceMapper mapper;

    @Override
    public List<Alert> findAll() {
        return mapper.toDomainList(jpaRepository.findAll());
    }

    @Override
    public Alert save(Alert alert) {
        AlertEntity entity = mapper.toEntity(alert);
        AlertEntity savedEntity = jpaRepository.save(entity);
        return mapper.toDomain(savedEntity);
    }

}
