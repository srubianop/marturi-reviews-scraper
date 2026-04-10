# Skill Registry — Reeviews Scraping

Auto-generated: 2026-04-09

## Project-Level Skills

| Name | Path | Description |
|------|------|-------------|
| ml-reviews-scraper | `.agent/skills/ml-reviews-scraper/SKILL.md` | Scrapes Mercado Libre reviews and exports Judge.me-compatible CSV with Colombian names, realistic emails, and image URLs |

## User-Level Skills (relevant)

| Name | Path | Description |
|------|------|-------------|
| ml-reviews-scraper | `~/.config/opencode/skills/ml-reviews-scraper/SKILL.md` | Same as project-level (duplicate, project-level wins) |

## SDD Skills (system)

| Name | Path | Description |
|------|------|-------------|
| sdd-init | `~/.config/opencode/skills/sdd-init/SKILL.md` | Initialize SDD context |
| sdd-explore | `~/.config/opencode/skills/sdd-explore/SKILL.md` | Explore and investigate before committing to a change |
| sdd-propose | `~/.config/opencode/skills/sdd-propose/SKILL.md` | Create change proposals |
| sdd-spec | `~/.config/opencode/skills/sdd-spec/SKILL.md` | Write specifications |
| sdd-design | `~/.config/opencode/skills/sdd-design/SKILL.md` | Create technical design |
| sdd-tasks | `~/.config/opencode/skills/sdd-tasks/SKILL.md` | Break down changes into tasks |
| sdd-apply | `~/.config/opencode/skills/sdd-apply/SKILL.md` | Implement tasks |
| sdd-verify | `~/.config/opencode/skills/sdd-verify/SKILL.md` | Verify implementation |
| sdd-archive | `~/.config/opencode/skills/sdd-archive/SKILL.md` | Archive completed changes |

## Project Conventions

- **No root AGENTS.md / CLAUDE.md / GEMINI.md / .cursorrules / copilot-instructions.md found**
- **License**: Apache-2.0
- **Code style**: Single-file procedural Python, CLI-first entrypoint
- **Dependencies**: Playwright (sync API), Python stdlib only
- **SDD config**: existing `openspec/config.yaml` marks testing as unavailable and `strict_tdd: false`
