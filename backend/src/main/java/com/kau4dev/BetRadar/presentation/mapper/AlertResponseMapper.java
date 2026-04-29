package com.kau4dev.BetRadar.presentation.mapper;

import com.kau4dev.BetRadar.domain.model.Alert;
import com.kau4dev.BetRadar.presentation.response.AlertResponse;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface AlertResponseMapper {

    AlertResponse toAlertResponse(Alert alert);

    List<AlertResponse> toAlertResponseList(List<Alert> alerts);

}