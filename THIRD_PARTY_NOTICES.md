# Third-party skill provenance

Vendored helper skills retain their upstream files and license notices where supplied. Exact upstream repositories and recorded hashes are listed in `skills-lock.json`:

- `canvas-design`: `anthropics/skills`;
- `shadcn`: `shadcn-ui/ui`;
- `vercel-react-best-practices`: `vercel-labs/agent-skills`;
- `web-design-guidelines`: `vercel-labs/agent-skills`.

The vendored `shadcn` frontmatter omits the non-standard `user-invocable` field so the package passes the current Codex skill schema. Its operational content is unchanged by that compatibility patch.

`design-taste-frontend` is an internal factory skill. Superpowers and Codex built-in skills are external runtime dependencies and are not redistributed by this repository.
