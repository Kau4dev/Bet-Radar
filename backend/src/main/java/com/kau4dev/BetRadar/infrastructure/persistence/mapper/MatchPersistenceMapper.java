package com.kau4dev.BetRadar.infrastructure.persistence.mapper;

import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface MatchPersistenceMapper {
    Match toDomain(MatchEntity entity);
    MatchEntity toEntity(Match domain);
    List<Match> toDomainList(List<MatchEntity> entities);
}
