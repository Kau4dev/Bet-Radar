package com.kau4dev.BetRadar.presentation.mapper;

import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.presentation.response.OddHistoryResponse;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface OddHistoryResponseMapper {

    OddHistoryResponse toOddHistoryResponse(OddHistory oddHistory);

    List<OddHistoryResponse> toOddHistoryResponseList(List<OddHistory> oddHistories);

}
