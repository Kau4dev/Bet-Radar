package com.kau4dev.BetRadar.presentation.controller;

import com.kau4dev.BetRadar.application.service.AuthService;
import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.presentation.request.CreateUserRequest;
import com.kau4dev.BetRadar.presentation.request.LoginRequest;
import com.kau4dev.BetRadar.presentation.response.CreateUserResponse;
import com.kau4dev.BetRadar.presentation.response.LoginResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        String token = authService.login(request.username(), request.password());
        return ResponseEntity.ok(new LoginResponse(token));
    }

    @PostMapping("/users")
    public ResponseEntity<CreateUserResponse> createUser(@Valid @RequestBody CreateUserRequest request) {
        User createdUser = authService.createUser(request.username(), request.password());
        return ResponseEntity.status(HttpStatus.CREATED).body(toUserResponse(createdUser));
    }

    @GetMapping("/users")
    public ResponseEntity<List<CreateUserResponse>> getUsers() {
        List<CreateUserResponse> users = authService.getUsers()
                .stream()
                .map(this::toUserResponse)
                .toList();

        return ResponseEntity.ok(users);
    }

    private CreateUserResponse toUserResponse(User user) {
        return new CreateUserResponse(
            user.id(),
            user.username(),
            user.role().name(),
            user.enabled()
        );
    }
}

