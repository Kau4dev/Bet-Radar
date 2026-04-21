package com.kau4dev.BetRadar.domain.repository;

import com.kau4dev.BetRadar.domain.model.User;

import java.util.List;
import java.util.Optional;

public interface UserRepository {

    Optional<User> findByUsername(String username);

    List<User> findAll();

    User save(User user);
}

