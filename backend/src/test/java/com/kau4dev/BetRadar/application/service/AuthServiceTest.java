package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.application.port.out.TokenGenerator;
import com.kau4dev.BetRadar.domain.exception.AuthenticationFailedException;
import com.kau4dev.BetRadar.domain.exception.UserAlreadyExistsException;
import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.domain.model.enums.UserRole;
import com.kau4dev.BetRadar.domain.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    AuthenticationManager authenticationManager;
    @Mock
    TokenGenerator tokenGenerator;
    @Mock
    UserRepository userRepository;
    @Mock
    PasswordEncoder passwordEncoder;
    @Mock
    Authentication authentication;

    private AuthService authService;

    @BeforeEach
    void setUp() {
        authService = new AuthService(authenticationManager, tokenGenerator, userRepository, passwordEncoder);
    }

    @Nested
    class Login {

        @Test
        @DisplayName("Deve autenticar e retornar token")
        void deveAutenticarERetornarToken() {
            doReturn(authentication).when(authenticationManager).authenticate(any(UsernamePasswordAuthenticationToken.class));
            doReturn("admin").when(authentication).getName();
            doReturn("token-123").when(tokenGenerator).generateToken("admin");

            String token = authService.login("  AdMin  ", "senha");

            assertEquals("token-123", token);

            ArgumentCaptor<UsernamePasswordAuthenticationToken> captor = ArgumentCaptor.forClass(UsernamePasswordAuthenticationToken.class);
            verify(authenticationManager).authenticate(captor.capture());
            assertEquals("admin", captor.getValue().getPrincipal());
        }

        @Test
        @DisplayName("Deve lancar excecao para credenciais invalidas")
        void deveLancarExcecaoParaCredenciaisInvalidas() {
             org.mockito.Mockito.doThrow(new BadCredentialsException("bad"))
                     .when(authenticationManager).authenticate(any(UsernamePasswordAuthenticationToken.class));

            AuthenticationFailedException ex = assertThrows(AuthenticationFailedException.class,
                    () -> authService.login("admin", "errada"));

            assertEquals("Credenciais invalidas", ex.getMessage());
        }

        @Test
        @DisplayName("Deve normalizar username nulo como vazio")
        void deveNormalizarUsernameNuloComoVazio() {
            doReturn(authentication).when(authenticationManager).authenticate(any(UsernamePasswordAuthenticationToken.class));
            doReturn("admin").when(authentication).getName();
            doReturn("token-123").when(tokenGenerator).generateToken("admin");

            authService.login(null, "senha");

            ArgumentCaptor<UsernamePasswordAuthenticationToken> captor = ArgumentCaptor.forClass(UsernamePasswordAuthenticationToken.class);
            verify(authenticationManager).authenticate(captor.capture());
            assertEquals("", captor.getValue().getPrincipal());
        }
    }

    @Nested
    class CreateUser {

        @Test
        @DisplayName("Deve criar usuario admin")
        void deveCriarUsuarioAdmin() {
            doReturn(Optional.empty()).when(userRepository).findByUsername("admin");
            doReturn("hash").when(passwordEncoder).encode("senha123");

            User saved = new User(UUID.randomUUID(), "admin", "hash", UserRole.ADMIN, true);
            doReturn(saved).when(userRepository).save(any(User.class));

            User created = authService.createUser("  AdMin ", "senha123");

            assertEquals("admin", created.username());
            assertEquals(UserRole.ADMIN, created.role());
            assertEquals("hash", created.passwordHash());
        }

        @Test
        @DisplayName("Deve lancar excecao quando usuario ja existe")
        void deveLancarExcecaoQuandoUsuarioJaExiste() {
            doReturn(Optional.of(new User(UUID.randomUUID(), "admin", "x", UserRole.ADMIN, true)))
                    .when(userRepository).findByUsername("admin");

            UserAlreadyExistsException ex = assertThrows(UserAlreadyExistsException.class,
                    () -> authService.createUser("admin", "senha"));

            assertEquals("Usuario ja cadastrado", ex.getMessage());
        }
    }

    @Nested
    class GetUsers {

        @Test
        @DisplayName("Deve retornar lista de usuarios")
        void deveRetornarListaDeUsuarios() {
            List<User> users = List.of(
                    new User(UUID.randomUUID(), "admin", "h1", UserRole.ADMIN, true),
                    new User(UUID.randomUUID(), "root", "h2", UserRole.ADMIN, false)
            );
            doReturn(users).when(userRepository).findAll();

            List<User> result = authService.getUsers();

            assertEquals(2, result.size());
        }
    }
}
