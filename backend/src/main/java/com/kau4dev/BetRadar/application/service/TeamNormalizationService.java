package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class TeamNormalizationService {

    private final Map<String, String> teamAliases = new ConcurrentHashMap<>();

    public TeamNormalizationService() {

        teamAliases.put("r. madrid", "Real Madrid");
        teamAliases.put("real madrid fc", "Real Madrid");
        teamAliases.put("barca", "Barcelona");
        teamAliases.put("fc barcelona", "Barcelona");
        teamAliases.put("s. paulo", "Sao Paulo");
        teamAliases.put("spfc", "Sao Paulo");
    }


    public String normalize(String rawName) {
        if (rawName == null || rawName.isBlank()) {
            throw new DomainValidationException("Nome do time nao pode ser nulo");
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