# Vélib' Pipeline

Petit projet perso pour apprendre à monter un pipeline de données de A à Z.
L'idée : récupérer en continu la dispo des Vélib' à Paris, la stocker dans
PostgreSQL, puis la transformer et l'analyser au fil des étapes.

Pour l'instant j'en suis à l'étape 1 : récupérer les données de l'API open
data Vélib' et les ranger telles quelles dans la base.

## Ce que fait le code

À chaque lancement, le script appelle deux endpoints de l'API :

- `station_information` : la liste des stations (nom, capacité, position...)
- `station_status` : combien de vélos et de places libres il y a dans chaque station

Les réponses sont stockées en JSON brut dans un schéma `raw`. Je ne transforme
rien à ce stade, ce sera le rôle de dbt à l'étape suivante.

Quelques détails :

- si l'API ne répond pas, le script réessaie 3 fois avant d'abandonner
- si une station n'a pas bougé depuis le dernier passage, elle n'est pas
  réinsérée (clé primaire sur `station_id` + `last_reported`)
- la liste des stations est simplement mise à jour à chaque fois

## Lancer le projet

Il faut Docker et Python 3.10 ou plus.

```bash
cp .env.example .env          # sous Windows : copy .env.example .env
docker compose up -d          # lance PostgreSQL

python -m venv .venv
source .venv/bin/activate     # sous Windows : .venv\Scripts\activate
pip install -r requirements.txt

pytest                        # les tests n'ont pas besoin de la base
python -m ingestion.load_raw  # récupère les données et les insère
```

Pour voir ce qui est arrivé dans la base :

```bash
docker exec -it velib_postgres psql -U velib -d velib
```

```sql
SELECT count(*) FROM raw.station_status;
SELECT payload->>'name', payload->>'capacity' FROM raw.station_information LIMIT 5;
```

## Organisation

```
ingestion/velib_client.py    appels à l'API
ingestion/load_raw.py        insertion dans PostgreSQL
sql/init/01_raw_schema.sql   création des tables au premier démarrage
tests/                       tests avec une API simulée
```

## La suite

- transformer les données avec dbt
- planifier la récupération automatiquement
- faire un petit dashboard
