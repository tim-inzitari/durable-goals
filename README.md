# Durable Goals

Durable Goals helps AI agents keep working toward the same goal across long
conversations, restarts, and multiple agent threads.

Instead of relying on chat history, it stores the goal, changes to the goal,
evidence, and completion rules in the repository. A small DAG can also expose
several independent goals so different threads can safely pick up different
work.

It does **not** run agents or choose models. It gives Codex, Claude Code, local
scripts, or another harness a shared answer to three questions:

- What is the current goal?
- What work is ready next?
- What evidence proves the goal is complete?

## Use it from your agent

If your agent harness discovers the included `update-durable-goal` skill, you
do not need to memorize the CLI. Just type what you want into the harness:

```text
Add a goal: build the Q4 sales plan, then create the hiring plan needed to
deliver it.
```

The harness records these as two ordered goals: the hiring plan becomes ready
after the sales plan is complete. You can use the same natural language to
update goals, record evidence, or connect more work. The skill translates the
request into durable files stored in your repository.

The basic convention is simple: an agent reads the goal package's `GOAL.md`
before acting. The repository remains the source of truth, even when the chat
or process disappears.

Canonical goal records are read-only after creation. Owner changes append a
numbered immutable revision; only `gateway.json` advances to reference the
latest history. Generated status and temporary workflow claims stay disposable.

## Install

Requires Python 3.11 or newer and has no runtime dependencies.

```bash
uv tool install durable-goals
```

Or install it with pip:

```bash
python -m pip install durable-goals
```

Then use the `dgoal` command anywhere:

```bash
dgoal --version
dgoal init goals/my-goal \
  --goal-id my-goal \
  --objective "Describe what needs to be finished."
```

## Try the example

The repository includes a prebuilt, multi-step model release goal covering
quality, safety, rollout, rollback readiness, and approval. The CLI does not
perform those tasks; it reads their checked-in evidence and shows how Durable
Goals interprets the result.

In the included files, a model scores `0.87` against an active `0.90`
requirement. The owner records a new `0.85` requirement, but it remains pending
until activation of the new goal target.

From a clone of this repository, run:

```bash
python -m pip install -e .

dgoal validate examples/model-refresh/gateway.json
dgoal status examples/model-refresh/gateway.json
dgoal resolve examples/model-refresh/gateway.json
```

- `validate` checks the goal package and its evidence.
- `status` summarizes current progress.
- `resolve` shows the active goal, desired goal, and pending changes together.

## What is included

- Persistent, versioned goal contracts
- Evidence-backed completion
- Append-only goal amendments and activation records
- DAG dependencies for multi-goal workflows
- Atomic claims so concurrent threads choose different ready goals
- A dependency-free Python CLI and test suite

## Learn more

Agents and maintainers should read [`AGENTS.md`](AGENTS.md) for the full
protocol, authority rules, CLI examples, and implementation scope.

- [CLI reference](docs/CLI.md)
- [Authoritative entry-point convention](docs/AUTHORITATIVE_ENTRYPOINT.md)
- [Distribution model](docs/DISTRIBUTION.md)
- [Cross-agent compatibility](docs/SKILL_COMPATIBILITY.md)

## Status

This is an early `0.1` release intended for trusted repositories. SHA-256
checks protect integrity, but they do not authenticate authors. Use signed
commits or another trusted transport when writers do not share the same trust
boundary.

Licensed under the [MIT License](LICENSE).
