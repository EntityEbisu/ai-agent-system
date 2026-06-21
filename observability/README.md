# Observability (v2 — deferred)

This directory is reserved for the self-hosted observability stack that is
deferred to a future phase.  The config files that used to live here
(``prometheus.yml``, ``loki-config.yml``) were for a Prometheus + Loki + Grafana
deployment that is not part of the v1 scope.

## Deferred stack

| Component   | Purpose                                      | Status     |
|-------------|----------------------------------------------|------------|
| Prometheus  | Scrape ``/metrics`` from the app             | DEFERRED   |
| Loki        | Collect structured JSON logs from stdout     | DEFERRED   |
| Grafana     | Dashboards for metrics & logs                | DEFERRED   |

## Current (v1) approach

- **Metrics:** ``GET /metrics`` returns Prometheus exposition format directly
  from the app process (``prometheus_client``).  No separate Prometheus server
  is needed for demo purposes.
- **Logs:** structured JSON logs are written to stdout via ``structlog``.
  Docker logs capture them — no Loki shipper needed yet.

## When v2 is scheduled

See ``DECISIONS.md`` at the repo root for the rationale and the intended
v2 design.
