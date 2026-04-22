package com.kau4dev.BetRadar.application.service;

import com.kau4dev.BetRadar.application.dto.RawOddDTO;
import com.kau4dev.BetRadar.domain.exception.DomainValidationException;
import com.kau4dev.BetRadar.domain.model.Bookmaker;
import com.kau4dev.BetRadar.domain.model.Match;
import com.kau4dev.BetRadar.domain.model.OddHistory;
import com.kau4dev.BetRadar.domain.repository.BookmakerRepository;
import com.kau4dev.BetRadar.domain.repository.MatchRepository;
import com.kau4dev.BetRadar.domain.repository.OddHistoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class OddProcessorServiceTest {

    @Mock
    BookmakerRepository bookmakerRepository;
    @Mock
    MatchRepository matchRepository;
    @Mock
    OddHistoryRepository oddHistoryRepository;
    @Mock
    MarketAnalyzerService marketAnalyzerService;
    @Mock
    TeamNormalizationService normalizer;

    private OddProcessorService service;

    @BeforeEach
    void setUp() {
        service = new OddProcessorService(
                bookmakerRepository,
                matchRepository,
                oddHistoryRepository,
                marketAnalyzerService,
                normalizer
        );
    }

    private RawOddDTO dto(String bookmaker, String teamHome, String teamAway, Double home, Double draw, Double away) {
        return new RawOddDTO(
                bookmaker,
                "external-id",
                teamHome,
                teamAway,
                new RawOddDTO.OddsDTO(home, draw, away),
                Instant.now()
        );
    }

    @Nested
    class ProcessAndStore {

        @Test
        @DisplayName("Deve processar e salvar criando entidades novas")
        void deveProcessarESalvarCriandoEntidadesNovas() {
            RawOddDTO dto = dto("Betano", "Real madrid fc", "barca", 2.2, 3.3, 3.4);

            doReturn("Real Madrid").when(normalizer).normalize("Real madrid fc");
            doReturn("Barcelona").when(normalizer).normalize("barca");

            doReturn(Optional.empty()).when(bookmakerRepository).findByName("Betano");
            Bookmaker savedBookmaker = new Bookmaker(UUID.randomUUID(), "Betano");
            doReturn(savedBookmaker).when(bookmakerRepository).save(any(Bookmaker.class));

            doReturn(Optional.empty()).when(matchRepository).findById("Real Madrid_v_Barcelona");
            Match savedMatch = new Match("Real Madrid_v_Barcelona", "Real Madrid", "Barcelona");
            doReturn(savedMatch).when(matchRepository).save(any(Match.class));

            doReturn(new OddHistory(UUID.randomUUID(), 2.2, 3.3, 3.4, dto.timestamp(), savedMatch, savedBookmaker))
                    .when(oddHistoryRepository).save(any(OddHistory.class));

            service.processAndStore(dto);

            ArgumentCaptor<OddHistory> captor = ArgumentCaptor.forClass(OddHistory.class);
            verify(oddHistoryRepository).save(captor.capture());
            assertEquals("Real Madrid_v_Barcelona", captor.getValue().match().id());
            assertEquals("Betano", captor.getValue().bookmaker().name());

            verify(marketAnalyzerService).calculateExpectedValue(
                    "Real Madrid_v_Barcelona",
                    "Betano",
                    2.2,
                    3.3,
                    3.4,
                    0.05
            );
            verify(marketAnalyzerService).detectSurebet("Real Madrid_v_Barcelona");
        }

        @Test
        @DisplayName("Deve processar usando bookmaker e match existentes")
        void deveProcessarUsandoBookmakerEMatchExistentes() {
            RawOddDTO dto = dto("Betano", "real madrid", "barcelona", 2.2, 3.3, 3.4);

            doReturn("Real Madrid").when(normalizer).normalize("real madrid");
            doReturn("Barcelona").when(normalizer).normalize("barcelona");

            Bookmaker existingBookmaker = new Bookmaker(UUID.randomUUID(), "Betano");
            Match existingMatch = new Match("Real Madrid_v_Barcelona", "Real Madrid", "Barcelona");
            doReturn(Optional.of(existingBookmaker)).when(bookmakerRepository).findByName("Betano");
            doReturn(Optional.of(existingMatch)).when(matchRepository).findById("Real Madrid_v_Barcelona");
            doReturn(new OddHistory(UUID.randomUUID(), 2.2, 3.3, 3.4, dto.timestamp(), existingMatch, existingBookmaker))
                    .when(oddHistoryRepository).save(any(OddHistory.class));

            service.processAndStore(dto);

            verify(bookmakerRepository).findByName("Betano");
            verify(matchRepository).findById("Real Madrid_v_Barcelona");
        }

        @Test
        @DisplayName("Deve lancar excecao quando dto for nulo")
        void deveLancarExcecaoQuandoDtoForNulo() {
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.processAndStore(null));
            assertEquals("payload de odds invalido", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao quando odds for nulo")
        void deveLancarExcecaoQuandoOddsForNulo() {
            RawOddDTO dto = new RawOddDTO("Betano", "m1", "A", "B", null, Instant.now());
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.processAndStore(dto));
            assertEquals("payload de odds invalido", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao quando bookmaker for invalido")
        void deveLancarExcecaoQuandoBookmakerForInvalido() {
            RawOddDTO dto = dto(" ", "A", "B", 2.0, 3.0, 3.0);
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.processAndStore(dto));
            assertEquals("bookmaker e obrigatorio", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao quando teams forem invalidos")
        void deveLancarExcecaoQuandoTeamsForemInvalidos() {
            RawOddDTO dto = dto("Betano", " ", "B", 2.0, 3.0, 3.0);
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.processAndStore(dto));
            assertEquals("teamHome e teamAway sao obrigatorios", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao quando timestamp for nulo")
        void deveLancarExcecaoQuandoTimestampForNulo() {
            RawOddDTO dto = new RawOddDTO("Betano", "m1", "A", "B", new RawOddDTO.OddsDTO(2.0, 3.0, 3.0), null);
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.processAndStore(dto));
            assertEquals("timestamp e obrigatorio", ex.getMessage());
        }

        @Test
        @DisplayName("Deve lancar excecao quando odds forem invalidas")
        void deveLancarExcecaoQuandoOddsForemInvalidas() {
            RawOddDTO dto = dto("Betano", "A", "B", -1.0, 3.0, 3.0);
            DomainValidationException ex = assertThrows(DomainValidationException.class, () -> service.processAndStore(dto));
            assertEquals("odds devem ser maiores que 0", ex.getMessage());
        }
    }
}

