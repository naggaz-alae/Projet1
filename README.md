# Vélib' Pipeline — disponibilité des vélos en temps réel

> README provisoire (étape 1/5). La version « recruteur » arrive à l'étape 5.

## Lancer l'étape 1

```bash
# 1. Configuration
cp .env.example .env            # Windows PowerShell : copy .env.example .env

# 2. Base de données PostgreSQL dans Docker
docker compose up -d
docker compose ps               # attendre STATUS = healthy

# 3. Environnement Python
python -m venv .venv
source .venv/bin/activate       # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# 4. Tests puis ingestion
pytest -v
python -m ingestion.load_raw
```

## Vérifier que les données sont arrivées

```bash
docker exec -it velib_postgres psql -U velib -d velib
```

```sql
SELECT count(*) FROM raw.station_status;
SELECT payload->>'name', payload->>'capacity' FROM raw.station_information LIMIT 5;
SELECT payload->'num_bikes_available_types' FROM raw.station_status LIMIT 3;
\q
```

## Structure

```
ingestion/velib_client.py   appel API + retries
ingestion/load_raw.py       écriture dans PostgreSQL (couche raw)
sql/init/01_raw_schema.sql  tables raw, créées au 1er démarrage
tests/                      tests unitaires (API simulée)
```
