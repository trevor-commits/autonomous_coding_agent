## 1. Freeze the companion contract

- [x] 1.1 Record the exact reviewed global commit, aggregate, wire-contract hash, and schema hash.
- [x] 1.2 Add the ACA-focused compatibility, canonicalization, hash, namespace, uniqueness, timestamp, TTL, and non-activation requirements.
- [x] 1.3 Copy the exact reviewed observation schema into the change packet.

## 2. Implement test first

- [x] 2.1 Add RED wake-v2 schema and wake-v1 compatibility tests.
- [x] 2.2 Add RED canonical hash, Unicode/order, duplicate, namespace, timestamp, skew, and TTL tests.
- [x] 2.3 Add the runtime observation-v2 schema and versioned wake-schema boundary.
- [x] 2.4 Add dependency-free semantic validation before ranking/authority.

## 3. Verify and land

- [x] 3.1 Run focused and full tests, schema parsing, compilation, OpenSpec, memory, and diff gates.
- [x] 3.2 Reconcile schema navigation, project memory, todo records, Ripple Check, and evidence.
- [x] 3.3 Obtain a fresh independent review-clean verdict and record findings/disposition.
- [x] 3.4 Re-verify, commit, push, open the PR, and prove remote-tip equality.
