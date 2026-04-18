package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.Bookmaker;

import java.util.Optional;

public interface BookmakerRepository {

    Optional<Bookmaker> findByName(String name);

    Bookmaker save(Bookmaker bookmaker);
}
