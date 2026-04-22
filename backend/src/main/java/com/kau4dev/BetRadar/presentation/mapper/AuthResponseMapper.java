package com.kau4dev.BetRadar.presentation.mapper;

import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.presentation.response.CreateUserResponse;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface AuthResponseMapper {

    CreateUserResponse toCreateUserResponse(User user);

    List<CreateUserResponse> toCreateUserResponseList(List<User> users);
}

