package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import com.kau4dev.BetRadar.infrastructure.entity.OddHistoryEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.OddHistoryJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class OddHistoryRepositoryAdapter implements OddHistoryRepository {

    private final OddHistoryJpaRepository jpaRepository;


    @Override
    public List<OddHistory> findLatestOddsForEachBookmaker(String matchId){
        return jpaRepository.findLatestOddsForEachBookmaker(matchId)
                .stream()
                .map(this::toDomain)
                .toList();
    }

    // puxar com querry dps
    @Override
    public List<OddHistory> findAll(){
        return jpaRepository.findAll()
                .stream()
                .map(this::toDomain)
                .toList();
    }

    @Override
    public OddHistory save(OddHistory oddHistory) {
        OddHistoryEntity saved = jpaRepository.save(toEntity(oddHistory));
        return toDomain(saved);
    }

    private OddHistory toDomain(OddHistoryEntity entity) {
        Match match = new Match(
                entity.getMatch().getId(),
                entity.getMatch().getTeamHome(),
                entity.getMatch().getTeamAway()
        );
        Bookmaker bookmaker = new Bookmaker(entity.getBookmaker().getId(), entity.getBookmaker().getName());

        return new OddHistory(
                entity.getId(),
                entity.getHomeWinOdd(),
                entity.getDrawOdd(),
                entity.getAwayWinOdd(),
                entity.getTimestamp(),
                match,
                bookmaker
        );
    }

    private OddHistoryEntity toEntity(OddHistory domain) {
        MatchEntity matchEntity = MatchEntity.builder()
                .id(domain.match().id())
                .teamHome(domain.match().teamHome())
                .teamAway(domain.match().teamAway())
                .build();

        BookmakerEntity bookmakerEntity = BookmakerEntity.builder()
                .id(domain.bookmaker().id())
                .name(domain.bookmaker().name())
                .build();

        return OddHistoryEntity.builder()
                .id(domain.id())
                .homeWinOdd(domain.homeWinOdd())
                .drawOdd(domain.drawOdd())
                .awayWinOdd(domain.awayWinOdd())
                .timestamp(domain.timestamp())
                .match(matchEntity)
                .bookmaker(bookmakerEntity)
                .build();
    }
}

