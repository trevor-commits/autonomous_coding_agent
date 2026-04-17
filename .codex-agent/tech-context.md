# Технический контекст

## Архетип проекта

Primary: `automation-script`
Supporting: `api-integration-worker`

## Стек

- Python 3.10+ supervisor runtime
- Codex CLI builder lane
- Linear routing and queue metadata
- Claude audit path
- Playwright verification
- repo docs + local artifacts as durable truth

## Ограничения

- Keep v1 narrow and deterministic.
- One writer and one browser owner remain non-negotiable.
- No broad hosted control plane, multi-writer flow, or Phase 5 hardening yet.
- Target-repo onboarding is the main dependency before broader execution claims.

## Интеграции

- Linear
- Codex CLI
- Claude access path
- Git
- Playwright

## Режим качества

сбалансированно

## Критерии качества

- repo truth stays aligned with plan
- queue and scope boundaries stay explicit
- verification requirements are named before execution
- env and dependency hygiene are documented
