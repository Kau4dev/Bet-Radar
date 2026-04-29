package com.kau4dev.BetRadar.presentation.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record LoginRequest(
        @NotBlank(message = "username e obrigatorio")
        @Size(min = 3, max = 40, message = "username deve ter entre 3 e 40 caracteres")
        @Pattern(regexp = "^[a-zA-Z0-9._-]+$", message = "username deve conter apenas letras, numeros, ponto, underscore ou hifen")
        String username,

        @NotBlank(message = "password e obrigatorio")
        @Size(min = 8, max = 72, message = "password deve ter entre 8 e 72 caracteres")
        @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d)\\S+$", message = "password deve conter letra, numero e nao pode ter espacos")
        String password
) {
}

