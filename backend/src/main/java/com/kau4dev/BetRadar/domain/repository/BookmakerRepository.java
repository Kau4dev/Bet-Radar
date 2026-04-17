package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface BookmakerRepository extends JpaRepository<BookmakerEntity, UUID> {

    Optional<BookmakerEntity> findByName(String name);
}
