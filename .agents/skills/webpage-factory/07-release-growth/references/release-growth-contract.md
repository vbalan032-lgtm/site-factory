# Release and growth record

Stage 7 does not create a sixth mandatory page artifact. Record the transition in canonical state and append-only history.

For every transition capture: page ID and route, selected mode, source and artifact fingerprints, starting and resulting status, checks and links, approval scope and timestamp when required, rollback target, release identifier when applicable, residual warnings, owner, and next action.

For `staging_prepare` and `production_release`, provide a rollback JSON object with the exact `page_id`, `route`, `release_id`, a non-empty `checkpoint`, and non-empty `restore_commands`. Do not put credentials, tokens, keys, passwords, or other secrets in this evidence.

For `production_release` and `growth_iteration`, validate the one canonical `docs/system/LOOP_LOG.md`. Record the previous byte length and `sha256:<digest>` of that exact prefix before appending. Validation must prove that the current file retains the hashed prefix and adds a UTF-8 entry containing the selected mode, release identifier, `page_id`, route, and exact starting-to-resulting status transition. A growth entry must also contain its `iteration_stage`. Two caller-selected history copies are not acceptable evidence.

For `growth_iteration`, additionally capture the evidence source, baseline, hypothesis, metric, guardrail, review window, selected earlier stage, and `iteration_stage`. Never edit an old release entry to describe a new deployment.
