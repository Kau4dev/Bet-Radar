package com.kau4dev.BetRadar.presentation.request;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateAlertRequest(

        @NotBlank(message = "matchId é obrigatório")
        String matchId,

        @NotBlank(message = "type é obrigatório")
        String type,

        @Size(max = 500, message = "description deve ter no máximo 500 caracteres")
        String description,

        @NotNull(message = "profitMargin é obrigatório")
        @DecimalMin(value = "0.0", inclusive = false, message = "profitMargin deve ser maior que 0")
        Double profitMargin
) {
}