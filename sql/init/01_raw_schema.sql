-- Couche RAW : on stocke la donnée telle que l'API la renvoie (JSON brut).
-- On ne transforme rien ici : les transformations viendront avec dbt (étape 2).

CREATE SCHEMA IF NOT EXISTS raw;

-- Disponibilités : change toutes les minutes -> une ligne par station et par relevé
CREATE TABLE IF NOT EXISTS raw.station_status (
    station_id      BIGINT       NOT NULL,
    last_reported   BIGINT       NOT NULL,   -- timestamp Unix fourni par l'API
    payload         JSONB        NOT NULL,   -- l'objet JSON complet de la station
    fetched_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    -- Idempotence : si la station n'a pas bougé depuis le dernier appel,
    -- on ne réinsère pas une ligne identique.
    PRIMARY KEY (station_id, last_reported)
);

-- Référentiel des stations : change rarement -> on écrase (upsert)
CREATE TABLE IF NOT EXISTS raw.station_information (
    station_id      BIGINT       PRIMARY KEY,
    payload         JSONB        NOT NULL,
    fetched_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
