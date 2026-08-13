# Review Checklist

Check for:

- User-visible behavior regressions.
- Public API, schema, type, route, or event contract breaks.
- Incorrect validation, auth, authorization, or tenancy assumptions.
- Data loss, duplicate writes, partial writes, or unsafe migrations.
- Race conditions, retries, idempotency gaps, and async ordering issues.
- Error handling that hides failures or leaks sensitive data.
- Test gaps for changed behavior and previous bug classes.
- Performance regressions on hot paths or large inputs.
