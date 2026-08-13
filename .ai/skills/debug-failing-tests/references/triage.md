# Failure Triage

Prefer this order:

1. Failing assertion or stack trace.
2. Test setup and fixtures.
3. Changed implementation.
4. Configuration, environment, dependency, or clock assumptions.
5. Flake signals: ordering, shared state, timeout, network, or random data.

Do not make tests less strict unless the expected behavior has intentionally changed and the plan says so.
