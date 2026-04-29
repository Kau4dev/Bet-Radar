package com.kau4dev.BetRadar.infrastructure.config.security;

import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.domain.model.enums.UserRole;
import com.kau4dev.BetRadar.domain.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Locale;

@Configuration
@RequiredArgsConstructor
public class  UserSeedConfig {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Value("${security.auth.seed.enabled:true}")
    private boolean seedEnabled;

    @Value("${security.auth.seed.username:admin}")
    private String seedUsername;

    @Value("${security.auth.seed.password:admin12345}")
    private String seedPassword;

    @Bean
    CommandLineRunner seedDefaultUser() {
        return args -> {
            if (!seedEnabled) {
                return;
            }

            String normalizedUsername = seedUsername.trim().toLowerCase(Locale.ROOT);
            if (userRepository.findByUsername(normalizedUsername).isPresent()) {
                return;
            }

            User adminUser = new User(
                    null,
                    normalizedUsername,
                    passwordEncoder.encode(seedPassword),
                    UserRole.ADMIN,
                    true
            );

            userRepository.save(adminUser);
        };
    }
}
