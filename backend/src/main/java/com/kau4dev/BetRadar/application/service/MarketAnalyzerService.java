package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.model.AlertType;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class MarketAnalyzerService {

    private final OddHistoryRepository oddHistoryRepository;
    private final AlertDispatcherService alertDispatcherService;

    /**
     * Calcula se a odd atual de uma casa está muito acima da média do mercado.
     * @param matchId ID da partida normalizada
     * @param currentOdd A odd que acabou de chegar
     * @param threshold Percentual de diferença (ex: 0.10 para 10%)
     */
    public void calculateExpectedValue(String matchId, Double currentOdd, Double threshold) {
        List<OddHistory> latestOdds = oddHistoryRepository.findLatestOddsForEachBookmaker(matchId);

        if (latestOdds.size() < 3) return;

        double averageMarketOdd = latestOdds.stream()
                .mapToDouble(OddHistory::homeWinOdd)
                .average()
                .orElse(0.0);

        double discrepancy = (currentOdd / averageMarketOdd) - 1;

        if (discrepancy >= threshold) {
            alertDispatcherService.dispatchOpportunity(
                    matchId,
                    AlertType.EV_PLUS,
                    "Odd da casa acima da media do mercado",
                    discrepancy * 100
            );
        }

    }

    /**
     * Detecta Arbitragem (Surebet): Lucro garantido cobrindo todos os resultados.
     * Fórmula: (1/OddCasa + 1/OddEmpate + 1/OddFora) < 1.0
     */
    public void detectSurebet(String matchId) {
        List<OddHistory> latestOdds = oddHistoryRepository.findLatestOddsForEachBookmaker(matchId);

        double bestHome = latestOdds.stream().mapToDouble(OddHistory::homeWinOdd).max().orElse(0.0);
        double bestDraw = latestOdds.stream().mapToDouble(OddHistory::drawOdd).max().orElse(0.0);
        double bestAway = latestOdds.stream().mapToDouble(OddHistory::awayWinOdd).max().orElse(0.0);

        if (bestHome == 0 || bestDraw == 0 || bestAway == 0) return;

        double arbitrageIndex = (1 / bestHome) + (1 / bestDraw) + (1 / bestAway);

        if (arbitrageIndex < 1.0) {
            double profitMargin = (1 - arbitrageIndex) * 100;
            alertDispatcherService.dispatchOpportunity(
                    matchId,
                    AlertType.SUREBET,
                    "Arbitragem detectada cobrindo 1X2",
                    profitMargin
            );
        }

    }
}