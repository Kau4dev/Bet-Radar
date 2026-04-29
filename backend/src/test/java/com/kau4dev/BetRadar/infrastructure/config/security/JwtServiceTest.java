package com.kau4dev.BetRadar.infrastructure.config.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class JwtServiceTest {

    private JwtService jwtService;

    @BeforeEach
    void setUp() {
        jwtService = new JwtService();
        // base64 de 32+ bytes para HS256
        ReflectionTestUtils.setField(jwtService, "secretKey", "YmV0cmFkYXItc3VwZXItc2VjcmV0LWp3dC1rZXktMjAyNi0zMmI=");
        ReflectionTestUtils.setField(jwtService, "expirationMs", 60_000L);
    }

    @Nested
    class TokenFlow {

        @Test
        @DisplayName("Deve gerar token valido e extrair username")
        void deveGerarTokenValidoEExtrairUsername() {
            String token = jwtService.generateToken("admin");

            assertTrue(jwtService.isTokenValid(token));
            assertEquals("admin", jwtService.extractUsername(token));
        }

        @Test
        @DisplayName("Deve retornar falso para token invalido")
        void deveRetornarFalsoParaTokenInvalido() {
            assertFalse(jwtService.isTokenValid("token-invalido"));
        }

        @Test
        @DisplayName("Deve retornar falso para token expirado")
        void deveRetornarFalsoParaTokenExpirado() throws InterruptedException {
            ReflectionTestUtils.setField(jwtService, "expirationMs", 1L);
            String token = jwtService.generateToken("admin");

            Thread.sleep(10);

            assertFalse(jwtService.isTokenValid(token));
        }
    }
}

