package com.kau4dev.BetRadar.infrastructure.persistence.repository;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.infrastructure.entity.AlertEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface AlertJpaRepository extends JpaRepository<AlertEntity, UUID> {
}
