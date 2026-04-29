package com.kau4dev.BetRadar.infrastructure.persistence.mapper;

import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.infrastructure.entity.OddHistoryEntity;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface OddHistoryPersistenceMapper {

    OddHistory toDomain(OddHistoryEntity entity);
    OddHistoryEntity toEntity(OddHistory domain);
    List<OddHistory> toDomainList(List<OddHistoryEntity> entities);
}
