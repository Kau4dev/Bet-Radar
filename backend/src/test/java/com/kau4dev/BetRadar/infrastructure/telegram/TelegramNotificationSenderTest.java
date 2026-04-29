package com.kau4dev.BetRadar.infrastructure.telegram;

import com.kau4dev.BetRadar.infrastructure.config.telegram.TelegramProperties;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TelegramNotificationSenderTest {

    @Mock
    TelegramProperties props;

    @Mock
    RestClient restClient;

    // Cadeia de mocks para RestClient fluent API
    @Mock
    RestClient.RequestBodyUriSpec requestBodyUriSpec;
    @Mock
    RestClient.RequestBodySpec requestBodySpec;
    @Mock
    RestClient.ResponseSpec responseSpec;

    private TelegramNotificationSender sender;

    @BeforeEach
    void setUp() {
        sender = new TelegramNotificationSender(props, restClient);
    }

    private void stubRestClientChain() {
        when(restClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodySpec);
        when(requestBodySpec.contentType(any(MediaType.class))).thenReturn(requestBodySpec);
        when(requestBodySpec.body(anyString())).thenReturn(requestBodySpec);
        when(requestBodySpec.retrieve()).thenReturn(responseSpec);
        when(responseSpec.toBodilessEntity()).thenReturn(null);
    }

    @Nested
    class Send {

        @Test
        @DisplayName("Nao deve enviar quando telegram.enabled=false")
        void naoDeveEnviarQuandoDesabilitado() {
            when(props.enabled()).thenReturn(false);

            sender.send("123456789", "mensagem teste");

            verify(restClient, never()).post();
        }

        @Test
        @DisplayName("Nao deve enviar sem chatId e sem defaultChatId configurado")
        void naoDeveEnviarSemChatId() {
            when(props.enabled()).thenReturn(true);
            when(props.defaultChatId()).thenReturn("");

            sender.send(null, "mensagem teste");

            verify(restClient, never()).post();
        }

        @Test
        @DisplayName("Deve usar defaultChatId quando destination for nulo")
        void deveUsarDefaultChatIdQuandoDestinationNulo() {
            when(props.enabled()).thenReturn(true);
            when(props.defaultChatId()).thenReturn("987654321");
            when(props.baseUrl()).thenReturn("https://api.telegram.org");
            when(props.token()).thenReturn("TOKEN123");
            stubRestClientChain();

            sender.send(null, "mensagem teste");

            verify(restClient).post();
            verify(requestBodySpec).body(contains("chat_id=987654321"));
        }

        @Test
        @DisplayName("Deve enviar com chatId explicito quando fornecido")
        void deveEnviarComChatIdExplicito() {
            when(props.enabled()).thenReturn(true);
            when(props.baseUrl()).thenReturn("https://api.telegram.org");
            when(props.token()).thenReturn("TOKEN123");
            stubRestClientChain();

            sender.send("111222333", "alerta surebet");

            verify(restClient).post();
            verify(requestBodySpec).body(contains("chat_id=111222333"));
        }

        @Test
        @DisplayName("Nao deve propagar excecao HTTP para o fluxo principal")
        void naoDevePropagarExcecaoHttp() {
            when(props.enabled()).thenReturn(true);
            when(props.baseUrl()).thenReturn("https://api.telegram.org");
            when(props.token()).thenReturn("TOKEN123");
            when(restClient.post()).thenReturn(requestBodyUriSpec);
            when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodySpec);
            when(requestBodySpec.contentType(any(MediaType.class))).thenReturn(requestBodySpec);
            when(requestBodySpec.body(anyString())).thenReturn(requestBodySpec);
            when(requestBodySpec.retrieve()).thenThrow(new RuntimeException("Telegram timeout"));

            // Nao deve lancar excecao
            sender.send("111222333", "mensagem");
        }
    }
}
