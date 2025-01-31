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

Summarize youtube videos, Wikipedia pages and many more.

## Data description

First dataset is available here : https://mmsum-dataset.github.io or in `/data/ref_data.csv`

- Note that the summaries in this dataset are strangely worded and extremely short.

Our handmade dataset is available here : `/data/new_ref_data_final.csv`

- The summaries have been generated using big models (GPT3.5 and Bart). The idea was to fine-tune the smaller models (to able to generate a summary fast on Docker using only cpu) using distillation.
- The urls for the youtube videos have been scraped using Requests (for each root_url, get recommended urls recursively) (script is in `/scripts/youtube-scraper.ipnyb`). An OpenAPI key is necessary for full automation (GPT3.5). The process has been automated on our Kaggle notebook (Bart).
