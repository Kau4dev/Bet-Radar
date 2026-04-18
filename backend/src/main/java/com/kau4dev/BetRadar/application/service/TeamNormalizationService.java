package com.kau4dev.BetRadar.application.service;

import org.springframework.stereotype.Service;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class TeamNormalizationService {

    private final Map<String, String> teamAliases = new ConcurrentHashMap<>();

    public TeamNormalizationService() {
        // Populando alguns exemplos de dicionário de sinônimos
        teamAliases.put("r. madrid", "Real Madrid");
        teamAliases.put("real madrid fc", "Real Madrid");
        teamAliases.put("barca", "Barcelona");
        teamAliases.put("fc barcelona", "Barcelona");
        teamAliases.put("s. paulo", "São Paulo");
        teamAliases.put("spfc", "São Paulo");
    }


    public String normalize(String rawName) {
        if (rawName == null || rawName.isBlank()) {
            throw new IllegalArgumentException("Nome do time não pode ser nulo");
        }

        String lowerCaseName = rawName.trim().toLowerCase();

        return teamAliases.getOrDefault(lowerCaseName, capitalize(lowerCaseName));
    }

    private String capitalize(String str) {
        if (str == null || str.isEmpty()) {
            return str;
        }
        return str.substring(0, 1).toUpperCase() + str.substring(1);
    }
}