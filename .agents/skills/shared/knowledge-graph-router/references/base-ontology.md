# Base ontology

Portable node types: `Project`, `Document`, `Source`, `Artifact`, `Page`, `Route`, `Entity`, `Offer`, `Audience`, `Claim`, `Evidence`, `Decision`, `Approval`, `Stage`, `Status`, `HandoffInput`, `Section`, `Component`, `Asset`.

Deterministic IDs use `project_id:type:normalized-key`. Every record retains `project_id`, source path, source fingerprint and properties. Every relationship retains type, provenance and confidence.

Provenance classes are `EXTRACTED`, `INFERRED`, and `AMBIGUOUS`. Deterministic lifecycle edges are `EXTRACTED` with confidence `1.0`. Project concepts belong in profile aliases or ontology extensions, not provider code.
