# Agency v2 observation contract companion

This is ACA Packet A: the consumer/validator half of the Agency v2 observation contract. It is intentionally inert until a separately reviewed global producer is bound to the exact compatible ACA SHA.

Normative source:

- global design commit: `4292f4efd4ce9c5a3586f51c63188c413e92025e`
- global review packet v3 aggregate: `056a4321a37a812d2054fb6f55c1673dda64086e96dd617805b3aca71ac74edc`
- global wire-contract SHA-256: `300c4f5625fe359c92b0f3ef20c2bd5a85de02c06dce7ab90a719b86843f84ee`
- global observation-schema SHA-256: `924dcf74ce336e5011af89fa9428fdac9d6254a6e3fddc0f5d00efe244790877`

The focused ACA rules are frozen in `contracts/agency-v2-packet-a.md`; the copied review schema is `contracts/partner-observation-v2.schema.json`. Runtime files must implement those rules exactly. This change does not add collectors, activate wake v2 globally, call a model, dispatch work, or widen authority.
