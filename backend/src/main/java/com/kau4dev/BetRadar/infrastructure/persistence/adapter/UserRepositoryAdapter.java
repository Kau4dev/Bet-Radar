package com.kau4dev.BetRadar.infrastructure.persistence.adapter;

import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.domain.repository.UserRepository;
import com.kau4dev.BetRadar.infrastructure.entity.UserEntity;
import com.kau4dev.BetRadar.infrastructure.persistence.mapper.UserPersistenceMapper;
import com.kau4dev.BetRadar.infrastructure.persistence.repository.UserJpaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class UserRepositoryAdapter implements UserRepository {

    private final UserJpaRepository jpaRepository;
    private final UserPersistenceMapper mapper;

    @Override
    public Optional<User> findByUsername(String username) {
        return jpaRepository.findByUsername(username)
                .map(mapper::toDomain);
    }

    @Override
    public List<User> findAll() {
        return jpaRepository.findAll().stream()
                .map(mapper::toDomain)
                .toList();
    }

    @Override
    public User save(User user) {
        UserEntity savedEntity = jpaRepository.save(mapper.toEntity(user));
        return mapper.toDomain(savedEntity);
    }
}


