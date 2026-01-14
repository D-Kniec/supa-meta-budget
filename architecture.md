# Architecture & System Design

This document details the technical infrastructure and data pipeline of the **supa-meta-budget** project.

---

## 1. System Architecture Diagram

```mermaid
---
config:
  layout: dagre
---
flowchart TB
 subgraph UserEnv["User Environment"]
    direction TB
        ua["User A (PyQt6 Desktop)  "]
        ub["User B (PyQt6 Desktop)"]
  end
 subgraph CloudSupabase["Supabase Cloud"]
    direction TB
        auth["Supabase Auth (JWT)"]
        db["PostgreSQL Instance (ACID Compliant)"]
        rls["Row Level Security (Access Control)"]
        views["Analytical SQL Views (Aggregation Layer)"]
  end
 subgraph DockerInfra["Docker Containerization"]
    direction TB
        meta["Metabase BI Engine"]
  end
    db -- "2. Identity Check (JWT Bound)" --> rls
    rls -- "3. Raw Data Persistence (RLS)" --> views
    views -- "4. Scheduled Data Polling (JDBC/Postgres)" --> meta
    meta -- "5. Visual Data Representation" --> dash["Interactive Dashboard (Browser)"]
    ua L_ua_auth_0@-- JWT Auth --> auth
    ub L_ub_auth_0@-- JWT Auth --> auth
    auth -- Authorizes Access --> db

    ua@{ shape: rect}
    ub@{ shape: rect}
    auth@{ shape: rect}
    db@{ shape: cyl}
    rls@{ shape: rect}
    views@{ shape: rect}
    meta@{ shape: rect}
    dash@{ shape: rect}
     db:::cloud
     meta:::docker
    classDef cloud fill:#e6fbe7,stroke:#2f9e44,stroke-width:2px
    classDef docker fill:#e0f0ff,stroke:#3182b7,stroke-width:2px
    style CloudSupabase fill:#e6fbe7,stroke:#2f9e44,stroke-width:2px
    style DockerInfra fill:#e0f0ff,stroke:#3182b7,stroke-width:2px

    L_ua_auth_0@{ curve: linear } 
    L_ub_auth_0@{ curve: linear }


    

