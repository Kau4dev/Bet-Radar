package com.kau4dev.BetRadar.infrastructure.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "bookmakers")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class BookmakerEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String name;
}
