# Release Checklist

Check:

- Required tests and build checks pass.
- Database migrations are reversible or have a documented recovery path.
- Config and secrets are present in target environments.
- Feature flags or rollout controls are understood.
- Backward compatibility is maintained for clients, jobs, schemas, and events.
- Observability is sufficient for diagnosing failures.
- Documentation and runbooks are updated when behavior or operations changed.
- Rollback plan is realistic and names any irreversible steps.
