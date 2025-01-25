# Projet_ML2

## Group members:

- Yanis Aumasson
- Maryem Jedid
- Clara Delianov
- Corentin Bohelay
- Gernido Hanampatra

## How to use

- Run Docker Desktop
- Execute (First time only, then no flags needed):

```bash
docker compose -f serving/docker-compose.yml up --build --force-recreate
```

```bash
docker compose -f webapp/docker-compose.yml up --build --force-recreate
```

```bash
docker compose -f reporting/docker-compose.yml up --build --force-recreate
```

- Webapp : http://localhost:8081/
- Reporting : http://localhost:8082/
- Serving API : http://localhost:8080/docs

Run if network issue between API and Webapp (run serving-api first):

```bash
docker compose down webapp/docker-compose.yml
```

If the reporting displays a white blank page or can't connect to localhost after a docker restart, try deleting localhost cookies.

## Description

## Data description
