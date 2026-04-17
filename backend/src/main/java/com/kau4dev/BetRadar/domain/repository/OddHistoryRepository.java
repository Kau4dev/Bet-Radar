package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface OddHistoryRepository extends JpaRepository<MatchEntity, UUID> {
}
