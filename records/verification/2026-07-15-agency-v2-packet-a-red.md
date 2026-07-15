# Agency v2 Packet A RED evidence

Date: 2026-07-15
Branch: `codex/agency-v2-packet-a`
Base: `282eb5118cfcd95263ffc9e409edce1ba831d623`
Coordinator: `019f5f11-5758-7790-b1b6-6f36cb50868f`
Linear: `self-contained: ER-141 Agency v2 Packet A observation contract.`

## Command

```bash
python3 -m unittest tests.test_partner_contracts -v
```

## Pre-implementation result

Exit: `1`

The focused suite ran 19 tests. Existing v1 identity, wake-safety, and executor-envelope tests passed. Six valid-v2 acceptance/boundary paths errored at the current v1-only schema with:

```text
PartnerContractError: observations.0: violates `additionalProperties` constraint; schema_version: violates `const` constraint
Ran 19 tests
FAILED (errors=6)
```

The failing valid-v2 paths covered:

- v1 unchanged plus valid-v2 acceptance;
- valid five-second observation skew;
- exact TTL boundary for each of the three collectors;
- canonical non-ASCII semantics with timestamp-only refresh stability.

The negative v2 cases were already rejection-shaped under the v1-only schema, so GREEN must be judged by the full matrix after v2 acceptance is implemented, not merely by preserving rejection.

## TDD disposition

This evidence was captured before runtime schema or semantic-loader implementation. The first HOTL run also exposed a quoted-negation command-encoding error; that orchestration error is preserved in `.hotl` state, while this durable artifact records the actual direct RED command and result used for the test-first gate.
