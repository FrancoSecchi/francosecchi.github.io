---
layout: post
title: "Por qué elegí FastAPI + SQLAlchemy para una API de salud"
description: "Primer post sobre health-metrics-api: el problema, el stack y los primeros trade-offs."
lang: es
tags: [health-metrics-api, python, fastapi]
---

<!--
Borrador: los archivos de _drafts/ no se publican.
Para publicarlo, movelo a _posts/ con la fecha adelante:
  _posts/2026-10-15-por-que-fastapi.md
-->

## El problema

Qué resuelve health-metrics-api y para quién (la clienta ficticia y su equipo).

## Por qué este stack

FastAPI, Pydantic, SQLAlchemy 2.0 y PostgreSQL: qué buscaba y qué descarté.

## El primer endpoint

```python
@app.post("/measurements", status_code=201)
def create_measurement(measurement: MeasurementIn) -> MeasurementOut:
    ...
```

## Lo que aprendí

## Lo que sigue
