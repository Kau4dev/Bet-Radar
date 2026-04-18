package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.repository.BookmakerRepository;
import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.BookmakerJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class BookmakerRepositoryAdapter implements BookmakerRepository {

    private final BookmakerJpaRepository jpaRepository;

    @Override
    public Optional<Bookmaker> findByName(String name) {
        return jpaRepository.findByName(name).map(this::toDomain);
    }

    @Override
    public Bookmaker save(Bookmaker bookmaker) {
        BookmakerEntity saved = jpaRepository.save(toEntity(bookmaker));
        return toDomain(saved);
    }

    private Bookmaker toDomain(BookmakerEntity entity) {
        return new Bookmaker(entity.getId(), entity.getName());
    }

    private BookmakerEntity toEntity(Bookmaker domain) {
        return BookmakerEntity.builder()
                .id(domain.id())
                .name(domain.name())
                .build();
    }
}

