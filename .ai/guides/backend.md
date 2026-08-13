# Backend Guide

Use this guide for APIs, services, jobs, persistence, domain logic, integrations, migrations, auth, authorization, and server-side tests.

## Structure

- Follow SOLID principles pragmatically.
- Separate responsibilities across controllers/routes, services/use cases, domain logic, repositories/data access, validators, serializers, jobs, and integration clients according to the project's conventions.
- Keep each module focused on one reason to change.
- Prefer dependency boundaries that make behavior testable without unnecessary infrastructure.
- Avoid mixing transport concerns, persistence concerns, business rules, and external integration details in the same unit.

## Implementation

- Preserve existing contracts, schemas, migrations, error shapes, and observability patterns.
- Keep validation and authorization explicit at the established boundary.
- Prefer idempotent operations and clear transaction boundaries for writes.
- Test domain rules, boundary behavior, failure modes, and integration contracts at the narrowest meaningful layer.
- When a task mixes API/backend behavior with UI, create separate subtasks for backend contract/logic and frontend consumption.
