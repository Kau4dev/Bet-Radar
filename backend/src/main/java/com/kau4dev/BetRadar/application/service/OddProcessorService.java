package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.application.dto.RawOddDTO;
import com.kau4dev.BetRadar.domain.repository.BookmakerRepository;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import com.kau4dev.BetRadar.infrastructure.entity.BookmakerEntity;
import com.kau4dev.BetRadar.infrastructure.entity.MatchEntity;
import com.kau4dev.BetRadar.infrastructure.entity.OddHistoryEntity;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.text.Normalizer;
import java.util.*;

@Service
@RequiredArgsConstructor
public class OddProcessorService {

    private final BookmakerRepository bookmakerRepository;
    private final MatchRepository matchRepository;
    private final OddHistoryRepository oddHistoryRepository;


    @Transactional
    public void processAndStore(RawOddDTO rawOddDTO){

        BookmakerEntity bookmaker = bookmakerRepository.findByName(rawOddDTO.bookmaker())
                .orElseGet(() -> bookmakerRepository.save(
                        BookmakerEntity.builder().name(rawOddDTO.bookmaker()).build()

                ));

        MatchEntity match = matchRepository.findById(rawOddDTO.matchId())
                .orElseGet(() -> matchRepository.save(
                        MatchEntity.builder()
                                .id(rawOddDTO.matchId())
                                .teamHome(rawOddDTO.teamHome())
                                .teamAway(rawOddDTO.teamAway())
                                .build()
                ));
        OddHistoryEntity history = OddHistoryEntity.builder()
                .match(match)
                .bookmaker(bookmaker)
                .homeWinOdd(rawOddDTO.odds().homeWin())
                .drawOdd(rawOddDTO.odds().draw())
                .awayWinOdd(rawOddDTO.odds().awayWin())
                .timestamp(rawOddDTO.timestamp())
                .build();

        oddHistoryRepository.save(history);
    }

    
    private static final Set<String> NOISE_TOKENS = Set.of(
            "fc", "sc", "ac", "cf", "club", "clube", "esporte", "sport"
    );

    private static final Map<String, String> TOKEN_ALIASES = Map.of(
            "s", "sao",
            "st", "saint"
    );

    public String normalizeTeamNames(String rawName) {
        if (rawName == null || rawName.isBlank()) {
            return "";
        }

        String normalized = Normalizer.normalize(rawName, Normalizer.Form.NFD)
                .replaceAll("\\p{M}+", "")
                .toLowerCase(Locale.ROOT)
                .replaceAll("[^a-z0-9]+", " ")
                .trim();

        if (normalized.isEmpty()) {
            return "";
        }

        List<String> canonicalTokens = new ArrayList<>();
        for (String token : normalized.split("\\s+")) {
            String canonical = TOKEN_ALIASES.getOrDefault(token, token);
            if (!NOISE_TOKENS.contains(canonical)) {
                canonicalTokens.add(canonical);
            }
        }

        return String.join("_", canonicalTokens);
    }

}
