package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.repository.BookmakerRepository;
import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.mapper.BookMakerPersistenceMapper;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.BookmakerJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class BookmakerRepositoryAdapter implements BookmakerRepository {

    private final BookmakerJpaRepository jpaRepository;
    private final BookMakerPersistenceMapper mapper;

    @Override
    public Optional<Bookmaker> findByName(String name) {
        return jpaRepository.findByName(name)
                .map(mapper::toDomain);
    }

    @Override
    public Bookmaker save(Bookmaker bookmaker) {
        BookmakerEntity entity = mapper.toEntity(bookmaker);
        BookmakerEntity saved = jpaRepository.save(entity);
        return mapper.toDomain(saved);
    }

}

