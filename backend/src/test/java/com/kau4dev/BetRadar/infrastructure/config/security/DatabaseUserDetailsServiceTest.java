package com.kau4dev.BetRadar.infrastructure.config.security;

import com.kau4dev.BetRadar.domain.model.User;
import com.kau4dev.BetRadar.domain.model.enums.UserRole;
import com.kau4dev.BetRadar.domain.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class DatabaseUserDetailsServiceTest {

    @Mock
    UserRepository userRepository;

    private DatabaseUserDetailsService service;

    @BeforeEach
    void setUp() {
        service = new DatabaseUserDetailsService(userRepository);
    }

    @Nested
    class LoadUserByUsername {

        @Test
        @DisplayName("Deve carregar usuario existente")
        void deveCarregarUsuarioExistente() {
            User user = new User(UUID.randomUUID(), "admin", "hash", UserRole.ADMIN, true);
            doReturn(Optional.of(user)).when(userRepository).findByUsername("admin");

            UserDetails details = service.loadUserByUsername("  AdMin  ");

            assertEquals("admin", details.getUsername());
            assertEquals("hash", details.getPassword());
            assertTrue(details.isEnabled());
            assertEquals(1, details.getAuthorities().size());
            verify(userRepository).findByUsername("admin");
        }

        @Test
        @DisplayName("Deve desabilitar usuario quando enabled for falso")
        void deveDesabilitarUsuarioQuandoEnabledForFalso() {
            User user = new User(UUID.randomUUID(), "admin", "hash", UserRole.ADMIN, false);
            doReturn(Optional.of(user)).when(userRepository).findByUsername("admin");

            UserDetails details = service.loadUserByUsername("admin");

            assertFalse(details.isEnabled());
        }

        @Test
        @DisplayName("Deve lancar excecao quando usuario nao existe")
        void deveLancarExcecaoQuandoUsuarioNaoExiste() {
            doReturn(Optional.empty()).when(userRepository).findByUsername("");

            UsernameNotFoundException ex = assertThrows(UsernameNotFoundException.class,
                    () -> service.loadUserByUsername(null));

            assertEquals("Usuario nao encontrado", ex.getMessage());
        }
    }
}

