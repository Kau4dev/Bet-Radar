package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.enums.AlertType;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;
import java.util.function.ToDoubleFunction;

@Slf4j
@Service
@RequiredArgsConstructor
public class MarketAnalyzerService {

    private final OddHistoryRepository oddHistoryRepository;
    private final AlertDispatcherService alertDispatcherService;

    public void calculateExpectedValue(
            String matchId,
            String bookmakerName,
            Double currentHomeOdd,
            Double currentDrawOdd,
            Double currentAwayOdd,
            Double threshold
    ) {
        List<OddHistory> latestOdds = oddHistoryRepository.findLatestOddsForEachBookmaker(matchId);

        if (latestOdds.size() < 2) {
            log.debug("EV ignorado para {}: mercado com poucas casas ({})", matchId, latestOdds.size());
            return;
        }

        evaluateOutcomeEv(matchId, bookmakerName, "HOME", currentHomeOdd, threshold, latestOdds, OddHistory::homeWinOdd);
        evaluateOutcomeEv(matchId, bookmakerName, "DRAW", currentDrawOdd, threshold, latestOdds, OddHistory::drawOdd);
        evaluateOutcomeEv(matchId, bookmakerName, "AWAY", currentAwayOdd, threshold, latestOdds, OddHistory::awayWinOdd);
    }

    private void evaluateOutcomeEv(
            String matchId,
            String bookmakerName,
            String outcome,
            Double currentOdd,
            Double threshold,
            List<OddHistory> latestOdds,
            ToDoubleFunction<OddHistory> extractor
    ) {
        if (currentOdd == null || currentOdd <= 0) {
            return;
        }

        double averageMarketOdd = latestOdds.stream()
                .filter(odd -> odd.bookmaker() != null && odd.bookmaker().name() != null)
                .filter(odd -> bookmakerName == null || !bookmakerName.equalsIgnoreCase(odd.bookmaker().name()))
                .mapToDouble(extractor)
                .filter(value -> value > 0)
                .average()
                .orElse(0.0);

        if (averageMarketOdd <= 0) {
            return;
        }

        double discrepancy = (currentOdd / averageMarketOdd) - 1;

        if (discrepancy >= threshold) {
            String description = String.format(
                    "Apostar %s na %s | Odd: %.2f | Media mercado: %.2f",
                    outcome, bookmakerName, currentOdd, averageMarketOdd
            );

            alertDispatcherService.dispatchOpportunity(
                    matchId,
                    AlertType.EV_PLUS,
                    description,
                    discrepancy * 100
            );

            log.info("EV+ detectado [{}] {}: oddAtual={}, media={}, discrepancia={}%%",
                    outcome, matchId, currentOdd, averageMarketOdd,
                    String.format("%.2f", discrepancy * 100));
        }
    }

    /**
     * Detecta Arbitragem (Surebet): Lucro garantido cobrindo todos os resultados.
     * Formula: (1/OddCasa + 1/OddEmpate + 1/OddFora) < 1.0
     * Inclui na mensagem: qual casa tem a melhor odd para cada resultado
     * e qual percentual do bankroll alocar em cada aposta.
     */
    public void detectSurebet(String matchId) {
        List<OddHistory> latestOdds = oddHistoryRepository.findLatestOddsForEachBookmaker(matchId);

        if (latestOdds.size() < 2) {
            log.debug("Surebet ignorado para {}: mercado com poucas casas ({})", matchId, latestOdds.size());
            return;
        }

        // Encontra a odd mais alta por resultado E qual bookmaker a oferece
        OddHistory bestHomeEntry = latestOdds.stream()
                .filter(o -> o.homeWinOdd() != null && o.homeWinOdd() > 0)
                .max(Comparator.comparingDouble(OddHistory::homeWinOdd))
                .orElse(null);

        OddHistory bestDrawEntry = latestOdds.stream()
                .filter(o -> o.drawOdd() != null && o.drawOdd() > 0)
                .max(Comparator.comparingDouble(OddHistory::drawOdd))
                .orElse(null);

        OddHistory bestAwayEntry = latestOdds.stream()
                .filter(o -> o.awayWinOdd() != null && o.awayWinOdd() > 0)
                .max(Comparator.comparingDouble(OddHistory::awayWinOdd))
                .orElse(null);

        if (bestHomeEntry == null || bestDrawEntry == null || bestAwayEntry == null) return;

        double bestHome = bestHomeEntry.homeWinOdd();
        double bestDraw = bestDrawEntry.drawOdd();
        double bestAway = bestAwayEntry.awayWinOdd();

        double arbitrageIndex = (1.0 / bestHome) + (1.0 / bestDraw) + (1.0 / bestAway);

        if (arbitrageIndex < 1.0) {
            double profitMargin = (1.0 - arbitrageIndex) * 100;

            // Percentual do bankroll a alocar em cada resultado
            double stakeHome = (1.0 / bestHome) / arbitrageIndex * 100;
            double stakeDraw = (1.0 / bestDraw) / arbitrageIndex * 100;
            double stakeAway = (1.0 / bestAway) / arbitrageIndex * 100;

            String homeBookmaker = bestHomeEntry.bookmaker() != null ? bestHomeEntry.bookmaker().name() : "?";
            String drawBookmaker = bestDrawEntry.bookmaker() != null ? bestDrawEntry.bookmaker().name() : "?";
            String awayBookmaker = bestAwayEntry.bookmaker() != null ? bestAwayEntry.bookmaker().name() : "?";

            String description = String.format(
                    "Casa: %.1f%% em %s (%.2f) | Empate: %.1f%% em %s (%.2f) | Fora: %.1f%% em %s (%.2f)",
                    stakeHome, homeBookmaker, bestHome,
                    stakeDraw, drawBookmaker, bestDraw,
                    stakeAway, awayBookmaker, bestAway
            );

            alertDispatcherService.dispatchOpportunity(
                    matchId,
                    AlertType.SUREBET,
                    description,
                    profitMargin
            );
        }
    }
}