# Promotions Service

[![CI Build](https://github.com/CSCI-GA-2820-FA26-001/promotions/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA26-001/promotions/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-FA26-001/promotions/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-FA26-001/promotions)

A RESTful microservice for managing **promotions** (discounts and special offers) for an e-commerce store. It is built with Flask and SQLAlchemy and is developed using test-driven development as part of the NYU DevOps class project.

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

| Method   | URL                | Description                                                   |
| -------- | ------------------ | ------------------------------------------------------------- |
| `GET`    | `/`                | Service name, version and URL of the promotions collection    |
| `POST`   | `/promotions`      | Create a promotion; returns `201` with a `Location` header    |
| `GET`    | `/promotions`      | List all promotions (the whole collection)                    |
| `GET`    | `/promotions/<id>` | Read a single promotion; `404` if it does not exist           |
| `PUT`    | `/promotions/<id>` | Update a promotion; `404` if it does not exist                |
| `DELETE` | `/promotions/<id>` | Delete a promotion; idempotent, always returns `204`          |

There are three `GET` routes because they return different things: `/` describes the service, `/promotions` returns every promotion as a JSON list, and `/promotions/<id>` returns one promotion. All endpoints are implemented.

Request bodies for `POST` and `PUT` are JSON using the fields above. `id`, `created_at` and `updated_at` are managed by the service and ignored if sent. `product_id` and `active` are optional.

Example:

```bash
curl -X POST http://localhost:8080/promotions \
  -H "Content-Type: application/json" \
  -d '{"name": "Summer Sale", "promotion_type": "PERCENTAGE_OFF", "value": 20, "start_date": "2026-06-01", "end_date": "2026-08-31"}'
```

### Errors

Errors are returned as JSON with `status`, `error` and `message` fields.

| Status | When                                                                               |
| ------ | ---------------------------------------------------------------------------------- |
| `400`  | Invalid or missing data (bad type, `value` rules violated, `end_date` before `start_date`, malformed body) |
| `404`  | Promotion id not found (read and update)                                           |
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
