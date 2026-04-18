package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.application.dto.RawOddDTO;
import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.BookmakerRepository;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class OddProcessorService {

    private final BookmakerRepository bookmakerRepository;
    private final MatchRepository matchRepository;
    private final OddHistoryRepository oddHistoryRepository;
    private final MarketAnalyzerService marketAnalyzerService;

    private final TeamNormalizationService normalizer;

    @Transactional
    public void processAndStore(RawOddDTO dto) {
        log.debug("Processando DTO recebido: {}", dto.matchId());

        String cleanTeamHome = normalizer.normalize(dto.teamHome());
        String cleanTeamAway = normalizer.normalize(dto.teamAway());
        String universalMatchId = cleanTeamHome + "_v_" + cleanTeamAway;

        Bookmaker bookmaker = bookmakerRepository.findByName(dto.bookmaker())
                .orElseGet(() -> bookmakerRepository.save(new Bookmaker(null, dto.bookmaker())));

        Match match = matchRepository.findById(universalMatchId)
                .orElseGet(() -> matchRepository.save(new Match(universalMatchId, cleanTeamHome, cleanTeamAway)));

        OddHistory history = new OddHistory(
                null,
                dto.odds().homeWin(),
                dto.odds().draw(),
                dto.odds().awayWin(),
                dto.timestamp(),
                match,
                bookmaker
        );

        oddHistoryRepository.save(history);
        log.info("Cotacao salva com sucesso para o jogo: {}", universalMatchId);

        marketAnalyzerService.calculateExpectedValue(universalMatchId, dto.odds().homeWin(), 0.10);
        marketAnalyzerService.detectSurebet(universalMatchId);
    }

}
