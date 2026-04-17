# Объяснение простыми словами

## Что происходит сейчас

The project now has its own local autopilot memory. I used the repo's real docs
to figure out what this project is actually building, then turned that into a
small set of plan options instead of guessing.

## Зачем это нужно

Without this step, the autopilot would keep acting like this repo was a generic
app. That would create the wrong plan. The point of this stage is to make sure
the next move matches the real project and its current bottleneck.

## Почему я задаю именно эти вопросы

One decision now matters more than the rest: whether to keep the next slice
inside this repo only, or to finally choose the first real target repo and move
the harness toward an end-to-end proof. That changes the honest next scope.

## Что действительно обязательно

- Keep the plan narrow.
- Preserve deterministic control and repo truth.
- Name the first target repo if the goal is real end-to-end progress.

## Что пока можно не делать

- Phase 4 Claude strategy
- Phase 5 memory/resume hardening
- generic platform or dashboard expansion

## Какой следующий шаг

Pick one plan variant. If you choose `Оптимально` or `С запасом`, also tell me
which repo should be the first implementation repo.
