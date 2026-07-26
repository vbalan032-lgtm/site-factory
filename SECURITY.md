# Security policy

- Never commit passwords, tokens, OAuth files, private keys, `.env` values, user Codex profiles, browser sessions, or absolute personal paths.
- Use OS environment variables or a user secret store for integrations.
- Treat website source documents as project-private unless their owner explicitly approves publication.
- Bootstrap never performs remote Git, release, staging, production, plugin installation, or credential migration.
- Release packaging uses an explicit source allowlist; rejects symlinks, Windows junctions, and other reparse points; and excludes `.env*` except `.env.example`, private-key formats, password/token/credential/OAuth-like names, secret directories, generated output, and `.site-factory/backups`.
- GitHub publication is a manually dispatched workflow behind the `release` Environment; configure a required reviewer before the first release.
- Report a suspected leak privately to the repository owner. Rotate the credential before rewriting history or publishing a fix.
