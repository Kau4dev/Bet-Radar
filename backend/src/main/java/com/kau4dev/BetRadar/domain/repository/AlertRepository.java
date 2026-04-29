package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.Alert;

import java.util.List;

public interface AlertRepository {

    List<Alert> findAll();

    Alert save(Alert alert);
}
