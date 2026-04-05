# YouTube ELT pipeline — architecture & roadmap

This document is a **memory map** of the project: what runs where, which tools are involved, and how work flows from local development toward Airflow, Postgres, testing, and CI/CD.

---

## 1. Big picture

You are building a **YouTube → extract/load → Postgres** pipeline, orchestrated with **Apache Airflow** in **Docker**, with a path toward **automated tests** and **CI/CD**.

---

## 2. System architecture (software & connections)

```mermaid
flowchart TB
  subgraph external["Outside Docker"]
    YT["YouTube Data API"]
    DEV["You — laptop / Git"]
  end

  subgraph docker["Docker Compose stack"]
    subgraph airflow["Airflow (custom image)"]
      WEB["airflow-webserver :8080"]
      SCH["airflow-scheduler"]
      WKR["airflow-worker Celery"]
      INIT["airflow-init migrations + admin user"]
    end
    REDIS["Redis broker :6379"]
    PG["PostgreSQL :5432"]

    subgraph pg_dbs["Three logical databases"]
      META[("airflow_metadata_db\nAirflow state")]
      CEL[("celery_results_db\nCelery results")]
      ELT[("elt_db\nYour warehouse / ELT data")]
    end
  end

  DEV -->|"docker compose, git, .env"| docker
  SCH --> REDIS
  WKR --> REDIS
  SCH --> META
  WKR --> META
  WKR --> CEL
  DAG["DAGs / Python tasks"] --> YT
  DAG --> ELT

  PG --- META
  PG --- CEL
  PG --- ELT

  WEB --> SCH
```

### Software by role

| Layer | Tools |
|--------|--------|
| Runtime / isolation | **Docker**, **Docker Compose** |
| Orchestration | **Apache Airflow 2.9.x** (**CeleryExecutor**) |
| Queue / workers | **Redis**, **Celery** (inside Airflow worker image) |
| Warehouse / stores | **PostgreSQL 13** — 3 DBs: metadata, Celery backend, **ELT** |
| Secrets / config | **`.env`** (not committed), variables referenced in **Compose** |
| DB bootstrap | **`docker/postgres/init-multiple-databases.sh`** (runs on Postgres **first** init only) |
| App image | **`Dockerfile`** extends **`apache/airflow`** + **`requirements.txt`** (+ project Python modules as needed) |
| Source API | **YouTube Data API** (`API_KEY`, `CHANNEL_HANDLE` via Airflow variables in compose) |

---

## 3. End-to-end startup flow

```mermaid
flowchart LR
  A["1. Define .env\n+ build/push image"] --> B["2. docker compose up"]
  B --> C["3. Postgres starts;\ninit script creates\n3 DBs + users"]
  C --> D["4. postgres healthy\npg_isready metadata DB"]
  D --> E["5. airflow-init runs\nmigrations + www user"]
  E --> F["6. webserver, scheduler,\nworker, redis running"]
  F --> G["7. DAGs in ./dags\nread YT API + write elt_db"]
```

### Commands you will reuse

| Goal | Command (run from project root with `.env` present) |
|------|-----------------------------------------------------|
| Build image (tag must match `.env` `DOCKERHUB_*` / `IMAGE_TAG` if you use that registry) | `docker build -t <namespace>/<repo>:<tag> .` |
| Push image | `docker push <namespace>/<repo>:<tag>` |
| Start stack | `docker compose up -d` |
| Stop (keep volumes / data) | `docker compose down` |
| Stop and **delete** Postgres data (re-runs init script on next up) | `docker compose down -v` |
| Airflow CLI (debug profile in `docker-compose.yaml`) | `docker compose --profile debug run --rm airflow-cli airflow ...` |
| Follow logs | `docker compose logs -f <service>` |

---

## 4. Data / ELT mental model

```mermaid
flowchart LR
  subgraph extract["Extract"]
    YT["YouTube API"]
  end
  subgraph transform_load["Transform + Load"]
    PY["Python in DAGs / tasks"]
  end
  subgraph store["Store"]
    ELT[("elt_db Postgres")]
  end
  YT --> PY --> ELT
```

Airflow **orchestrates** jobs; it does not replace Postgres. Tasks call the YouTube API and **load** into **`elt_db`**. The **metadata** and **Celery** databases exist for Airflow/Celery internals, not as your primary analytics store (unless you choose otherwise).

---

## 5. Repo layout vs what containers see

```mermaid
flowchart TB
  subgraph repo["Git repository"]
    DC["docker-compose.yaml"]
    ENV[".env gitignored"]
    DAGF["dags/"]
    DOCK["docker/postgres/init-multiple-databases.sh"]
    IMG["Dockerfile + requirements.txt"]
  end
  subgraph containers["Container paths"]
    OF["/opt/airflow/dags, logs, plugins, ..."]
  end
  DAGF -->|"bind mount"| OF
  DOCK -->|"mounted to postgres\n/docker-entrypoint-initdb.d"| PGINIT["Postgres first boot only"]
```

---

## 6. Roadmap (where you are → next)

```mermaid
flowchart TB
  P1["Foundation\n• Repo + .env\n• Compose: Postgres, Redis, Airflow\n• Multi-DB init script\n• Custom Airflow image"] --> P2["Airflow\n• DAGs in dags/\n• Variables + warehouse Postgres connection\n• Schedule + monitor in UI"]
  P2 --> P3["Warehouse\n• Design elt_db schema\n• Load from API into tables"]
  P3 --> P4["Testing\n• pytest in tests/\n• DAG / task tests\n• Postgres in CI if required"]
  P4 --> P5["CI/CD\n• GitHub Actions: lint, test, build, push image\n• Align local .env with CI secrets/variables"]
```

---

## 7. One-sentence summary

**A Dockerized Airflow cluster (webserver, scheduler, Celery workers, Redis) uses Postgres for three databases; an init script creates app DBs on first boot; DAGs extract from YouTube and load into `elt_db`; testing and CI/CD automate quality and deployment next.**

---

## Viewing Mermaid diagrams

- [GitHub renders Mermaid in Markdown](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/) in `.md` files on the web.
- VS Code / Cursor: install a “Mermaid” preview extension if previews do not show by default.

---

## Related files in this repo

| File / path | Role |
|-------------|------|
| `docker-compose.yaml` | Services, env, volumes, healthchecks |
| `.env` | Secrets and parameters (local only; not committed) |
| `docker/postgres/init-multiple-databases.sh` | Creates metadata, Celery, and ELT DBs + users on first Postgres init |
| `Dockerfile` | Airflow-based image with extra Python dependencies |
| `dags/` | Airflow DAG definitions |
| `tests/` | Automated tests (to grow with the project) |
