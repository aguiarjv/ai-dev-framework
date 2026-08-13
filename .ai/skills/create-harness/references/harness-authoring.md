# Harness Authoring

Use this reference for non-trivial harnesses.

## Safety

- Default to local, deterministic validation.
- Gate mutating operations behind explicit flags.
- Never hardcode secrets.
- Treat production services as out of scope unless the user explicitly requests them.

## Shape

Good harnesses:

- explain usage through `--help`;
- validate required tools and files before running expensive commands;
- print the command or mode being run;
- fail fast with useful messages;
- clean up only files they created;
- document prerequisites in `.ai/harnesses/registry.md`.

## Registry Maintenance

Update the existing entry when the harness purpose is unchanged. Create a new entry when the command validates a distinct workflow or has materially different prerequisites.

If a harness supersedes another, keep the old entry briefly with a maintenance note naming the replacement.
