# Варианты плана

Перед утверждением плана предложи пользователю три варианта и коротко объясни разницу.

## Минимум

- Что входит:
  - bootstrap `.codex-agent` and keep the repo-local project memory truthful
  - close the branch/Linear lifecycle reset (`GIL-55`)
  - keep the next slice inside this repo only, without choosing a target repo yet
- Когда выбирать: if you want to stabilize governance and control-plane posture
  first, while intentionally keeping target-repo work deferred
- Чего точно не будет:
  - no target-repo Phase 0 onboarding
  - no Phase 3 UI-verification slice
  - no Phase 4 or Phase 5 work

## Оптимально

- Что входит:
  - everything in `Минимум`
  - choose the first real implementation repo
  - complete the truthful Phase 0 path for that repo: contract, manual baseline,
    CI parity note, and tool readiness
  - then move into one bounded Phase 3 app-launch/UI-verification slice
- Когда выбирать: if the goal is real movement toward the first end-to-end
  proof instead of more internal preparation
- Чего точно не будет:
  - no Phase 4 bounded Claude strategy
  - no Phase 5 memory/resume hardening
  - no broad platformization beyond one real repo family

## С запасом

- Что входит:
  - everything in `Оптимально`
  - webhook/reconciliation-ready intake scaffolding after the first target repo
    baseline is real
  - stronger audit packet preparation around the same bounded milestone
- Когда выбирать: if you can afford one extra reliability layer before Claude
  strategy, but still want to keep the control plane narrow
- Что не должно расползтись:
  - Phase 4 and Phase 5 still stay out
  - no multi-writer or broad hosted control plane
  - no generic "platform" rewrite

## Что рекомендовано по умолчанию

- Выбранный вариант: `Оптимально`
- Почему: it closes the most important current truth gap. This repo already has
  meaningful Phase 1/2 work, so staying repo-local forever would protect the
  docs but still postpone the actual proof. `Оптимально` keeps the scope
  bounded while finally naming the first real repo needed to prove the harness.
