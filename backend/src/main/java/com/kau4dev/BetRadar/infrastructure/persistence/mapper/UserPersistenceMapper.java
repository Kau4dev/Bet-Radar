package com.kau4dev.BetRadar.infrastructure.persistence.mapper;

import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.infrastructure.entity.UserEntity;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface UserPersistenceMapper {

    User toDomain(UserEntity entity);

    UserEntity toEntity(User domain);
}
