# **YouTube API — ELT Pipeline**

## **Architecture**

Diagrams and service topology are documented in [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md).

## **Overview**

A containerized **ELT-style** pipeline that ingests YouTube channel metadata and video statistics, orchestrates workloads with **Apache Airflow**, persists data in **PostgreSQL** staging and core layers, and validates quality with **SODA**. The stack is defined with **Docker Compose**; **GitHub Actions** automates image builds and test runs.

## **Data source**

The pipeline uses the **YouTube Data API**. Channel scope is driven by configuration (handle / channel identity). The following fields are modeled end-to-end:

- Video ID  
- Title  
- Upload date  
- Duration  
- View count  
- Like count  
- Comment count  

Staging retains API-shaped values; core applies typed columns and derived attributes (e.g. duration as time, video category such as Shorts vs normal length).

## **Pipeline summary**

1. **Extract** — Python tasks call the YouTube API and write structured JSON extracts.  
2. **Load (staging)** — JSON is loaded into a **staging** schema in PostgreSQL (`yt_api`).  
3. **Transform & load (core)** — Rows are transformed and merged into a **core** schema for analytics-oriented consumption.  
4. **Quality** — SODA scans run against both layers (missing keys, duplicates, basic consistency checks).  

Initial runs perform full loads; subsequent scheduled runs **upsert** mutable metrics and reconcile deletions relative to the latest API snapshot.

## **Tools & technologies**

| Layer | Stack |
|--------|--------|
| *Containerization* | **Docker**, **Docker Compose** |
| *Orchestration* | **Apache Airflow** (CeleryExecutor, **Redis**) |
| *Warehouse* | **PostgreSQL** 13 |
| *Languages* | **Python**, **SQL** |
| *Data quality* | **Soda Core** (Postgres) |
| *Testing* | **pytest** |
| *CI/CD* | **GitHub Actions** |

## **Containerization**

The project extends the official **Airflow Docker** baseline with a custom image (`Dockerfile` + `requirements.txt`). Compose brings up Airflow webserver, scheduler, Celery workers, Redis, and PostgreSQL. Airflow connections and variables are supplied via environment variables (`AIRFLOW_CONN_*`, `AIRFLOW_VAR_*`); sensitive values are kept out of version control (`.env`, not committed). A Fernet key is used for Airflow’s internal secret handling.

## **Orchestration**

Three DAGs run in sequence (extract → warehouse load → quality):

| DAG | Role |
|-----|------|
| *produce_json* | Fetches from the API and materializes JSON under the Airflow data volume. |
| *update_db* | Loads staging, transforms, and refreshes core tables. |
| *data_quality* | Executes SODA scans on staging and core. |

The Airflow UI is available at `http://localhost:8080` when the stack is running locally.

## **Data storage**

Warehouse data lives in PostgreSQL (`elt_db`), with **staging** and **core** schemas. The same database host also hosts Airflow metadata and Celery result backends (separate databases). Data can be inspected with `psql`, **DBeaver**, or any Postgres client pointed at the composed service.

## **Testing**

Automated tests cover Airflow DAG loading, connection configuration, pure Python warehouse helpers, optional integration checks against the API and database, and lightweight CLI-level validation where the runtime allows. **SODA** enforces checks in the `data_quality` DAG.

## **CI/CD**

**GitHub Actions** (`.github/workflows/ci-cd.yaml`) builds and pushes the custom image when relevant files change, brings up Compose on the runner with injected secrets, runs **pytest**, and optionally runs Airflow DAG smoke tests. Manual workflow dispatch supports skipping CLI DAG tests when the environment has no same-day extract file.

## **Portfolio artifacts**

Screenshots and architecture graphics live under **`docs/images/`** (Airflow DAG views, successful runs, warehouse samples).

---

*Private portfolio project — configuration via `.env.example`; secrets are not stored in the repository.*
