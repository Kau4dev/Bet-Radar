package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.application.dto.RawOddDTO;
import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.BookmakerRepository;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class OddProcessorService {

    private static final double EV_THRESHOLD = 0.05;

    private final BookmakerRepository bookmakerRepository;
    private final MatchRepository matchRepository;
    private final OddHistoryRepository oddHistoryRepository;
    private final MarketAnalyzerService marketAnalyzerService;

    private final TeamNormalizationService normalizer;

    @Transactional
    @CacheEvict(cacheNames = {"matches", "timeline", "opportunities"}, allEntries = true)
    public void processAndStore(RawOddDTO dto) {
        validateInput(dto);
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

        marketAnalyzerService.calculateExpectedValue(
                universalMatchId,
                dto.bookmaker(),
                dto.odds().homeWin(),
                dto.odds().draw(),
                dto.odds().awayWin(),
                EV_THRESHOLD
        );
        marketAnalyzerService.detectSurebet(universalMatchId);
    }

    private void validateInput(RawOddDTO dto) {
        if (dto == null || dto.odds() == null) {
            throw new DomainValidationException("payload de odds invalido");
        }

        if (dto.bookmaker() == null || dto.bookmaker().isBlank()) {
            throw new DomainValidationException("bookmaker e obrigatorio");
        }

        if (dto.teamHome() == null || dto.teamHome().isBlank() || dto.teamAway() == null || dto.teamAway().isBlank()) {
            throw new DomainValidationException("teamHome e teamAway sao obrigatorios");
        }

        if (dto.timestamp() == null) {
            throw new DomainValidationException("timestamp e obrigatorio");
        }

        if (dto.odds().homeWin() == null || dto.odds().draw() == null || dto.odds().awayWin() == null
                || dto.odds().homeWin() <= 0 || dto.odds().draw() <= 0 || dto.odds().awayWin() <= 0) {
            throw new DomainValidationException("odds devem ser maiores que 0");
        }
    }
}
