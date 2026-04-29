package com.kau4dev.BetRadar.presentation.mapper;

import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.presentation.response.MatchResponse;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface MatchResponseMapper {

    MatchResponse toMatchResponse(Match match);

    List<MatchResponse> toMatchResponseList(List<Match> matches);

}
