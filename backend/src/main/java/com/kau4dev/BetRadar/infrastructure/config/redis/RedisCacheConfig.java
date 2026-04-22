package com.kau4dev.BetRadar.infrastructure.config.redis;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.CacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Configuration
public class RedisCacheConfig {

    @Bean
    public CacheManager cacheManager(
            RedisConnectionFactory connectionFactory,
            @Value("${app.cache.ttl.matches-seconds:30}") long matchesTtlSeconds,
            @Value("${app.cache.ttl.timeline-seconds:30}") long timelineTtlSeconds,
            @Value("${app.cache.ttl.opportunities-seconds:15}") long opportunitiesTtlSeconds
    ) {
        RedisCacheConfiguration defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
                .serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer()))
                .disableCachingNullValues();

        Map<String, RedisCacheConfiguration> cacheConfigs = new HashMap<>();
        cacheConfigs.put("matches", defaultConfig.entryTtl(Duration.ofSeconds(matchesTtlSeconds)));
        cacheConfigs.put("timeline", defaultConfig.entryTtl(Duration.ofSeconds(timelineTtlSeconds)));
        cacheConfigs.put("opportunities", defaultConfig.entryTtl(Duration.ofSeconds(opportunitiesTtlSeconds)));

        return RedisCacheManager.builder(connectionFactory)
                .cacheDefaults(defaultConfig)
                .withInitialCacheConfigurations(cacheConfigs)
                .build();
    }
}

