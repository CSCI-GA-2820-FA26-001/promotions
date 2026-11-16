# Promotions Service

[![CI Build](https://github.com/CSCI-GA-2820-FA26-001/promotions/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA26-001/promotions/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-FA26-001/promotions/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-FA26-001/promotions)

A RESTful microservice for managing **promotions** (discounts and special offers) for an e-commerce store. It is built with Flask, Flask-RESTX and SQLAlchemy and is developed using test-driven development as part of the NYU DevOps class project.

## Overview

A promotion describes a discount that can apply to a single product or to the whole store. The goal of this service is to provide a clean REST API to Create, Read, Update, Delete and List promotions, so that other services (such as the shopping cart or order services) can look up which promotions are running.

### The Promotion model

| Field            | Type     | Description                                                          |
| ---------------- | -------- | -------------------------------------------------------------------- |
| `id`             | integer  | Unique id, assigned by the database                                  |
| `name`           | string   | Name of the promotion (required, max 63 characters)                  |
| `promotion_type` | enum     | `PERCENTAGE_OFF`, `AMOUNT_OFF` or `BOGO`                             |
| `value`          | number   | Percent or currency amount off; must be `>= 0`, `<= 100` for `PERCENTAGE_OFF`, and `0` for `BOGO` |
| `product_id`     | integer  | Product the promotion applies to; `null` means store-wide            |
| `start_date`     | date     | First day the promotion runs (ISO format, inclusive)                 |
| `end_date`       | date     | Last day the promotion runs (inclusive, must not be before the start)|
| `active`         | boolean  | Whether the promotion is enabled (defaults to `true`)                |
| `created_at`     | datetime | Set automatically                                                    |
| `updated_at`     | datetime | Set automatically                                                    |

### API endpoints

| Method   | URL                                  | Description                                                   |
| -------- | ------------------------------------ | ------------------------------------------------------------- |
| `GET`    | `/`                                  | Service name, version and URL of the promotions collection    |
| `GET`    | `/health`                            | Liveness/readiness probe; returns `200` with `{"status": "OK"}` |
| `GET`    | `/apidocs/`                          | Swagger UI documenting the endpoints and data models          |
| `POST`   | `/api/promotions`                    | Create a promotion; returns `201` with a `Location` header    |
| `GET`    | `/api/promotions`                    | List promotions, optionally filtered (see below)              |
| `GET`    | `/api/promotions/<id>`               | Read a single promotion; `404` if it does not exist           |
| `PUT`    | `/api/promotions/<id>`               | Update a promotion; `404` if it does not exist                |
| `DELETE` | `/api/promotions/<id>`               | Delete a promotion; idempotent, always returns `204`          |
| `PUT`    | `/api/promotions/<id>/activate`      | Set `active` to `true`; `404` if it does not exist            |
| `PUT`    | `/api/promotions/<id>/deactivate`    | Set `active` to `false`; `404` if it does not exist           |

The REST API is built with [Flask-RESTX](https://flask-restx.readthedocs.io/) and lives under `/api`; the interactive Swagger documentation is at `/apidocs/` (the raw spec is at `/api/swagger.json`). `/` and `/health` are plain routes outside `/api`: `/` describes the service and `/health` reports that the service is up (used by Kubernetes probes).

`GET /api/promotions` accepts the query parameters `id`, `promotion_type`, `value`, `product_id`, `start_date`, `end_date` and `active`. Multiple parameters are combined with AND, unknown parameters are ignored, and an unparseable value returns `400`.

Request bodies for `POST` and `PUT` are JSON using the fields above. `id`, `created_at` and `updated_at` are managed by the service and ignored if sent. `product_id` and `active` are optional.

Example:

```bash
curl -X POST http://localhost:8080/api/promotions \
  -H "Content-Type: application/json" \
  -d '{"name": "Summer Sale", "promotion_type": "PERCENTAGE_OFF", "value": 20, "start_date": "2026-06-01", "end_date": "2026-08-31"}'
```

### Errors

Every error, including unknown URLs, is returned as JSON with `status`, `error` and `message` fields.

| Status | When                                                                               |
| ------ | ---------------------------------------------------------------------------------- |
| `400`  | Invalid or missing data (bad type, `value` rules violated, `end_date` before `start_date`, malformed body) |
| `404`  | Promotion id not found (read, update, activate and deactivate)                     |
| `405`  | HTTP method not allowed for the URL                                                |
| `415`  | `Content-Type` is not `application/json`                                           |
| `500`  | Unexpected server error                                                            |

## Getting Started

### Prerequisites

- Python 3
- A PostgreSQL database (the included VS Code dev container sets this up for you)

The easiest way to get a working environment is to open the repo in VS Code and choose **Reopen in Container**.

### Setup

```bash
make install           # install dependencies
cp dot-env-example .env  # optional: environment variables for Flask
```

The database connection is read from the `DATABASE_URI` environment variable (see `service/config.py`).

### Running

```bash
make run               # start the service on http://localhost:8080
make test              # run the unit tests
make lint              # run flake8 and pylint
```

Run `make help` to see all available targets, including the Docker and Kubernetes (K3D) deployment targets.

### Deploying to local Kubernetes

The application image is built from the repository's root `Dockerfile` and pushed to the local K3D registry at `localhost:5001`. The Kubernetes nodes use the registry's internal address, `cluster-registry:5000`. Override `REGISTRY_PORT` if host port 5001 is already in use. A PostgreSQL database must be deployed first; see [Story #32](https://github.com/CSCI-GA-2820-FA26-001/promotions/issues/32) for its manifests and Secret setup.

```bash
make cluster

# Create this Secret once, using the database name and Service from Story #32.
DB_PASSWORD="$(python -c 'import secrets; print(secrets.token_hex(16))')"
kubectl create secret generic promotions-postgres \
  --from-literal=password="$DB_PASSWORD" \
  --from-literal=database-uri="postgresql+psycopg://postgres:${DB_PASSWORD}@postgres:5432/promotions"
unset DB_PASSWORD

kubectl apply -f k8s/postgres/
kubectl rollout status statefulset/postgres --timeout=180s

make build
make push
make deploy
```

The Ingress is available at `http://promotions.local:8080`. When the hostname does not resolve locally, send the expected host header:

```bash
curl -H 'Host: promotions.local' http://127.0.0.1:8080/health
```

The health endpoint is supplied by [Story #23](https://github.com/CSCI-GA-2820-FA26-001/promotions/issues/23) and is used for the Kubernetes startup, readiness, and liveness probes.

## Contents

```text
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to fix Windows CRLF issues
.devcontainer/      - Support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
Pipfile             - list of Python libraries required by the code
Makefile            - common development and deployment tasks
Procfile            - gunicorn process definition
setup.cfg           - tool configuration
wsgi.py             - WSGI entry point for the service

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - Promotion model, validation and database queries
├── routes.py              - REST API routes
└── common                 - common code package
    ├── cli_commands.py    - Flask command to recreate all tables
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for the Promotion model
└── test_routes.py         - test suite for service routes
```

## Contributing

Work is tracked as GitHub issues using the **User Story** template. Create a branch per story, add tests first, and make sure `make test` and `make lint` pass before opening a pull request.
