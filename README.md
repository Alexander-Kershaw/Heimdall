***
# HEIMDALL
***

**Engineering Delivery Intelligence system.**

- **BIFROST**: ingestion + raw → staging (in later milestones)
- **MIDGARD**: Postgres warehouse
- **Superset**: dashboard suite (**VALSKJALF / HUGINN / MUNINN / GJALLARHORN**)

## Milestone 0: Boot the stack

### Prereqs
- Docker and Docker Compose

### Setup

From repo root:

```bash
cp .env.example .env
make up
make ps
```

For logs:

```bash
make logs
```

---