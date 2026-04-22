package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.domain.exception.AuthenticationFailedException;
import com.kau4dev.BetRadar.domain.exception.UserAlreadyExistsException;
import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.domain.model.enums.UserRole;
import com.kau4dev.BetRadar.domain.repository.UserRepository;
import com.kau4dev.BetRadar.application.port.out.TokenGenerator;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Locale;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final TokenGenerator tokenGenerator;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public String login(String username, String password) {
        String normalizedUsername = normalizeUsername(username);

        try {
            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(normalizedUsername, password)
            );
            return tokenGenerator.generateToken(authentication.getName());
        } catch (BadCredentialsException ex) {
            throw new AuthenticationFailedException("Credenciais invalidas");
        }
    }

    public User createUser(String username, String rawPassword) {
        String normalizedUsername = normalizeUsername(username);
        if (userRepository.findByUsername(normalizedUsername).isPresent()) {
            throw new UserAlreadyExistsException("Usuario ja cadastrado");
        }

        User userToCreate = new User(
                null,
                normalizedUsername,
                passwordEncoder.encode(rawPassword),
                UserRole.ADMIN,
                true
        );

        return userRepository.save(userToCreate);
    }

    public List<User> getUsers() {
        return userRepository.findAll();
    }

    private String normalizeUsername(String username) {
        return username == null ? "" : username.trim().toLowerCase(Locale.ROOT);
    }
}

