# Plan: Refactor Promotions API using Flask-RESTX and Swagger (Issue #35)

## Goal

Refactor the Promotions REST API from plain Flask to Flask-RESTX with no functional change. Move the REST endpoints under `/api`, serve Swagger docs at `/apidocs/`, return JSON for all HTTP errors, and keep test coverage at or above 95%.

## Current state

- `service/routes.py` is plain Flask.
  - `GET /` and `GET /health` are utility routes.
  - Seven `/promotions` routes: `POST` and `GET` on the collection; `GET`, `PUT` and `DELETE` on `/promotions/<id>`; `PUT` on `/<id>/activate` and `/<id>/deactivate`.
  - The list endpoint takes query filters (`id`, `promotion_type`, `value`, `product_id`, `start_date`, `end_date`, `active`). Bad values return 400 through helper parsers. Unknown filters are ignored.
- `service/common/error_handlers.py` has JSON handlers for 400, 404, 405, 415 and 500, plus `DataValidationError`. The body shape is `{status, error, message}`.
- `service/models.py` does validation in `Promotion.deserialize()`, which raises `DataValidationError`.
- `service/__init__.py` imports `routes` and `error_handlers` inside `create_app()` using `current_app`.
- `tests/test_routes.py` hardcodes `/promotions...`, `/` and `/health`. `setup.cfg` enforces `--cov-fail-under=95`.
- k8s probes use `/health`. The ingress routes `/` to the service. The README documents the old paths.

## Decisions

1. `/health` and `/` stay where they are. The k8s probes depend on `/health`. The `url` field returned by `/` changes to `/api/promotions`.
2. The old `/promotions` paths are removed, with no aliases. This is a breaking change for consumers.
3. Swagger UI is served at `/apidocs/` via `doc="/apidocs/"` on the `Api` object.
4. The error body stays `{status, error, message}` so clients see no change. Flask-RESTX intercepts exceptions on `/api` before Flask's `errorhandler`s, so it needs its own handlers.

## Steps

1. **Dependency.** Add `flask-restx` to the `Pipfile` and re-lock. Use a version compatible with Flask 3.1 and Werkzeug 3.1.
2. **`service/__init__.py`.** Create `api = Api(app, version="1.0", title="Promotions REST API Service", doc="/apidocs/", prefix="/api")`. Register the routes and error handlers against it.
3. **`service/routes.py` rewrite.**
   - Define `create_model` (the input fields) and `promotion_model` (which adds `id`, `created_at` and `updated_at`). Declare `value` as `fields.Float` so output matches `serialize()`, and `promotion_type` as an enum.
   - Keep `_parse_filters` for identical query behavior, and document the params with `@api.doc(params=...)`.
   - Add `Resource` classes: `PromotionCollection` (GET, POST), `PromotionResource` (GET, PUT, DELETE), `ActivateResource` and `DeactivateResource`.
   - Keep `/` and `/health` as plain Flask routes.
   - Keep the `Location` header on 201, the idempotent 204 on DELETE, the `request.is_json` 415 check, and the rollback on a failed update.
4. **`service/common/error_handlers.py`.** Register `@api.errorhandler(DataValidationError)` and handlers for the HTTP errors, returning the existing JSON shape. Keep the Flask-level handlers so 404 and 405 on non-API URLs are also JSON.
5. **Tests.**
   - Update `tests/test_routes.py` to use the `/api/promotions` prefix, keeping the assertions the same as regression proof.
   - Add tests for `/apidocs/` returning 200, `/swagger.json` listing the paths and models, JSON bodies on 404 and 405, and the new `url` in the index.
   - Run `make test` and confirm coverage is at or above 95%.
6. **Docs and BDD.** Update the README endpoint table, curl examples and Swagger link. Confirm `features/steps` doesn't depend on old paths.
7. **Lint.** Run `make lint` (flake8 and pylint).

## Risks

- **Error handler precedence.** A wrong RESTX handler registration could fall back to RESTX's default `{"message": ...}` body. Add one test per status code (400, 404, 405, 415, 500).
- **`value` as Decimal.** `serialize()` returns `float`, so the model declares `fields.Float`.
- **Malformed JSON.** The message may differ slightly from today. The status stays 400, and the existing tests only check the status.

## Acceptance criteria (from the issue)

1. All existing CRUD, Query and Action operations work under `/api`.
2. `/apidocs/` shows the endpoints and data models.
3. Invalid data returns an appropriate JSON error.
4. The test suite passes with at least 95% coverage.
