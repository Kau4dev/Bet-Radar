package com.kau4dev.BetRadar;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@Disabled("Unit-test suite: contexto completo depende de infra externa (DB/Kafka)")
@SpringBootTest
class BetRadarApplicationTests {

	@Test
	void contextLoads() {
	}

}
