package com.kau4dev.BetRadar.infrastructure.persistence.mapper;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.infrastructure.entity.AlertEntity;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface AlertPersistenceMapper {

    Alert toDomain(AlertEntity entity);

    AlertEntity toEntity(Alert alert);

    List<Alert> toDomainList(List<AlertEntity> entities);

    default AlertType map(String value) {
        return value == null ? null : AlertType.fromValue(value);
    }

    default String map(AlertType value) {
        return value == null ? null : value.name();
    }
}
