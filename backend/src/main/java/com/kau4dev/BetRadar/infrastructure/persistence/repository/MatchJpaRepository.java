package com.kau4dev.BetRadar.infrastructure.persistence.repository;

import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MatchJpaRepository extends JpaRepository<MatchEntity, String> {
}

