# Supa-Meta-Budget

High-concurrency OLTP desktop application for collaborative financial management, focusing on data integrity, transaction isolation, and real-time visual analytics.

## Tech Stack
* Frontend: Python / PyQt6
* Database: Supabase (PostgreSQL) optimized for OLTP
* Analytics: Metabase (Self-hosted via Docker)
* Infrastructure: Docker Compose, Python Multithreading

## Engineering Key Features
* OLTP & Data Integrity: Full ACID compliance implemented through PostgreSQL transaction isolation levels and row-level locking to manage simultaneous multi-user database access.
* Non-Blocking UI: Asynchronous architecture using QThread worker patterns to offload database I/O from the main GUI thread, preventing interface freezing.
* System Design: Modular architecture following Repository and Service patterns to ensure decoupling and simplified unit testing.
* Containerized BI: Integration of Metabase via Docker for advanced SQL-based financial reporting and automated dashboards.


## System Design:
Detailed in the accompanying `architecture.md`, focusing on decoupling and scalability.

## Project Structure
```text
supa-meta-budget/
├── .env
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── README.md
├── architecture.md
├── assets/
│   ├── icons/
│   ├── img/
│   └── qss/
├── database/
│   ├── migrations/
│   └── seed/
├── docker/
│   └── metabase/
├── scripts/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── core/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── ui/
│   └── utils/
└── tests/
    ├── test_services/
    └── test_repositories/