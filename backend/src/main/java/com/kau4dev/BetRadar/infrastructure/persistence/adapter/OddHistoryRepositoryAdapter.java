package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import com.kau4dev.BetRadar.infrastructure.entity.OddHistoryEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.mapper.OddHistoryPersistenceMapper;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.BookmakerJpaRepository;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.MatchJpaRepository;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.OddHistoryJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
@RequiredArgsConstructor
public class OddHistoryRepositoryAdapter implements OddHistoryRepository {

    private final OddHistoryJpaRepository jpaRepository;
    private final OddHistoryPersistenceMapper mapper;
    private final MatchJpaRepository matchJpaRepository;
    private final BookmakerJpaRepository bookmakerJpaRepository;


    @Override
    public List<OddHistory> findLatestOddsForEachBookmaker(String matchId) {
        return jpaRepository.findLatestOddsForEachBookmaker(matchId)
                .stream()
                .map(mapper::toDomain)
                .toList();
    }

    @Override
    public List<OddHistory> findAll() {
        return mapper.toDomainList(jpaRepository.findAll());
    }

    @Override
    public OddHistory save(OddHistory oddHistory) {
        MatchEntity managedMatch = resolveManagedMatch(oddHistory.match());
        BookmakerEntity managedBookmaker = resolveManagedBookmaker(oddHistory.bookmaker());

        OddHistoryEntity entity = OddHistoryEntity.builder()
                .id(oddHistory.id())
                .homeWinOdd(oddHistory.homeWinOdd())
                .drawOdd(oddHistory.drawOdd())
                .awayWinOdd(oddHistory.awayWinOdd())
                .timestamp(oddHistory.timestamp())
                .match(managedMatch)
                .bookmaker(managedBookmaker)
                .build();

        OddHistoryEntity savedEntity = jpaRepository.save(entity);
        return mapper.toDomain(savedEntity);
    }

    @Override
    public long deleteByTimestampBefore(Instant threshold) {
        return jpaRepository.deleteByTimestampBefore(threshold);
    }

    private MatchEntity resolveManagedMatch(Match match) {
        if (match == null || match.id() == null || match.id().isBlank()) {
            throw new DomainValidationException("match e obrigatorio para salvar odd history");
        }

        return matchJpaRepository.findById(match.id())
                .orElseGet(() -> matchJpaRepository.save(
                        MatchEntity.builder()
                                .id(match.id())
                                .teamHome(match.teamHome())
                                .teamAway(match.teamAway())
                                .build()
                ));
    }

    private BookmakerEntity resolveManagedBookmaker(Bookmaker bookmaker) {
        if (bookmaker == null || bookmaker.name() == null || bookmaker.name().isBlank()) {
            throw new DomainValidationException("bookmaker e obrigatorio para salvar odd history");
        }

        return bookmakerJpaRepository.findByName(bookmaker.name())
                .orElseGet(() -> bookmakerJpaRepository.save(
                        BookmakerEntity.builder()
                                .id(bookmaker.id())
                                .name(bookmaker.name())
                                .build()
                ));
    }

}

