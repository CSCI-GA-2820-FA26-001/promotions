
# PostgreSQL on Local Kubernetes

This directory contains the PostgreSQL StatefulSet and Service for the Promotions application.

## Setup

Create the local Kubernetes cluster using `make cluster`.

Generate a local database password and create the Kubernetes Secret:

```bash
DB_PASSWORD="$(python -c 'import secrets; print(secrets.token_hex(16))')"

kubectl create secret generic promotions-postgres \
  --from-literal=password="$DB_PASSWORD" \
  --from-literal=database-uri="postgresql+psycopg://postgres:${DB_PASSWORD}@postgres:5432/promotions"

unset DB_PASSWORD
```

Do not commit actual database credentials.

Deploy PostgreSQL:

```bash
kubectl apply -f k8s/postgres/
kubectl rollout status statefulset/postgres --timeout=180s
```

Verify:

```bash
kubectl get pods
kubectl get svc
kubectl get pvc
```

Connection settings:

- Service: postgres
- Port: 5432
- Database: promotions
- User: postgres
- Secret: promotions-postgres
- Secret keys: password, database-uri

The PostgreSQL StatefulSet uses a persistent volume claim to preserve database data when its Pod is recreated.
