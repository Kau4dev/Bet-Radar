package com.kau4dev.BetRadar.infrastructure.persistence.mapper;

import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import org.mapstruct.Mapper;


@Mapper(componentModel = "spring")
public interface BookMakerPersistenceMapper {

    Bookmaker toDomain(BookmakerEntity entity);
    BookmakerEntity toEntity(Bookmaker domain);
}
