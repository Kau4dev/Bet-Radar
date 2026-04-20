package com.kau4dev.BetRadar.presentation.mapper;

import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.presentation.response.MatchResponse;
import com.kau4dev.BetRadar.presentation.response.OddHistoryResponse;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface MatchResponseMapper {
    MatchResponse toMatchResponse(Match match);
    List<MatchResponse> toMatchResponseList(List<Match> matches);

    OddHistoryResponse toOddHistoryResponse(OddHistory oddHistory);
    List<OddHistoryResponse> toOddHistoryResponseList(List<OddHistory> list);
}
