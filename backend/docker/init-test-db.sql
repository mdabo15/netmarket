-- Exécuté automatiquement au tout premier démarrage du conteneur Postgres
-- (volume vide), en plus de la base POSTGRES_DB créée par l'image officielle.
-- Isole les données de test de celles de développement : les tests font un
-- drop_all/create_all à chaque lancement (voir backend/tests/conftest.py).
CREATE DATABASE netmarket_test;
