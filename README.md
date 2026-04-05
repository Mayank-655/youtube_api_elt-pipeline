# YouTube API → ELT pipeline

End-to-end data pipeline: extract channel/video metadata from the **YouTube Data API**, orchestrate with **Apache Airflow** (Celery + Redis), load into **PostgreSQL** (`staging` / `core` schemas), and run **SODA** data-quality checks. **Docker Compose** packages the stack; **GitHub Actions** builds the image and runs tests.

## Architecture

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for diagrams, services, and data flow.

Optional: add a high-level diagram image here, for example `docs/images/architecture.png`, and reference it below.

```markdown
![Architecture](docs/images/architecture.png)
```

## Screenshots

Add images under `docs/images/` (e.g. Airflow DAG graph, successful run, staging/core tables in your SQL client) and link them here for recruiters.

| Area        | Suggested capture                          |
|------------|-----------------------------------------------|
| Airflow    | DAG grid, task graph, successful `produce_json` run |
| Warehouse  | `staging.yt_api` / `core.yt_api` sample rows   |
| Data quality | SODA scan success in task logs              |

Example:

```markdown
![DAG overview](docs/images/airflow-dag.png)
```

## Tech stack

- **Python**, **Docker**, **Docker Compose**
- **Apache Airflow** 2.9.x (CeleryExecutor, Redis)
- **PostgreSQL** 13 (Airflow metadata, Celery backend, `elt_db`)
- **SODA** (checks in `include/soda/`)
- **pytest**, **GitHub Actions** (`.github/workflows/ci-cd.yaml`)

## Quick start (local)

1. Copy **`.env.example`** → **`.env`** and set secrets, API key, channel handle, Docker image coordinates, and `FERNET_KEY`.
2. Build the custom Airflow image (match `DOCKERHUB_NAMESPACE` / `DOCKERHUB_REPOSITORY` / `IMAGE_TAG` in `.env`).
3. `docker compose up -d`
4. Open **http://localhost:8080**, unpause DAGs, run or wait for the schedule.

Do **not** commit `.env` (it is gitignored).

## Repository layout

| Path | Role |
|------|------|
| `dags/` | DAG definitions (`produce_json`, `update_db`, `data_quality`) and Python modules |
| `docker/postgres/` | Multi-database init for Airflow + `elt_db` |
| `include/soda/` | SODA configuration and checks |
| `tests/` | Unit, functional, integration, and e2e-style tests |

## License

Add a `LICENSE` file if you want to specify terms for reuse of this portfolio project.
