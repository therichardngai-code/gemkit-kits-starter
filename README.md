# GemKit Kits Starter

AI-powered development tools for Gemini CLI. Provides specialized agents, skills/extensions, hooks, and workflows to supercharge your AI-assisted development.

## Installation

```bash
npx gemkit-cli init 
```

Or manually clone into your project:

```bash
git clone https://github.com/therichardngai-code/gemkit-kits-starter 
```

## Features

### Agents

Pre-configured AI agents for specialized tasks:

| Agent | Description | Use For |
|-------|-------------|---------|
| `code-executor` | Plan-driven, test-driven code implementation | Feature development, bug fixes, refactoring |
| `researcher` | Multi-step technical research with source validation | Best practices, technology comparisons, deep dives |
| `tester` | Comprehensive test generation and coverage analysis | Unit tests, integration tests, E2E, coverage gaps |

### Commands

Quick-access slash commands:

| Command | Description |
|---------|-------------|
| `/code` | Start coding & testing an existing plan with orchestrated workflow |
| `/test` | Run tests locally and analyze summary report |
| `/paste/image` | Paste image from clipboard for analysis |

### Extensions/Skills

Domain-specific knowledge and patterns:

| Skill | Description |
|-------|-------------|
| `spawn-agent` | Intelligent BM25 search for optimal agent-skill combinations |
| `frontend-development` | React 19, TanStack Query/Router, MUI v7, Zustand, Vitest |
| `backend-development` | Node.js, Python, APIs, OAuth 2.1, PostgreSQL, security |
| `frontend-design` | Creative UI/UX with modern CSS, animations, distinctive aesthetics |
| `testing` | Vitest, Jest, Playwright, MSW, coverage analysis |
| `research` | Technical investigation with source validation and report generation |

### Hooks

Automated session lifecycle and tool control:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `gk-session-init` | SessionStart, BeforeAgent, BeforeModel | Initialize/resume sessions, capture context |
| `gk-session-end` | SessionEnd | Track session completion and metrics |
| `gk-scout-block` | Tool calls | Block access to directories in `.gkignore` |
| `gk-dev-rules-reminder` | BeforeAgent | Inject development rules and session context |
| `gk-discord-notify` | SessionEnd | Send Discord notifications on completion |

## Project Structure

```
.gemini/
├── agents/                    # Agent definitions
│   ├── code-executor.md       # Implementation agent
│   ├── researcher.md          # Research agent
│   └── tester.md              # Testing agent
├── commands/                  # Slash commands
│   ├── code.toml              # /code command
│   ├── test.toml              # /test command
│   └── paste/image.toml       # /paste/image command
├── extensions/                # Skills with reference docs
│   ├── spawn-agent/           # Agent spawning with BM25 search
│   ├── frontend-development/  # Frontend patterns
│   ├── backend-development/   # Backend patterns
│   ├── frontend-design/       # UI/UX design
│   ├── testing/               # Testing patterns
│   └── research/              # Research methodology
├── hooks/                     # Session lifecycle hooks
│   ├── gk-session-init.cjs    # Session initialization
│   ├── gk-session-end.cjs     # Session cleanup
│   ├── gk-scout-block.cjs     # Directory blocking
│   ├── gk-dev-rules-reminder.cjs
│   ├── lib/                   # Shared utilities
│   └── notifications/         # Discord notifications
└── .env                       # Session state (auto-generated)

.agent/workflows/              # Claude Code workflows
├── code.md                    # Orchestrated coding workflow

settings.json                  # Tool and hook configuration
.gk.json                       # GemKit configuration
.gkignore                      # Blocked directories
```

## Configuration

### settings.json

Controls tool permissions and hooks:

```json
{
  "tools": {
    "enableHooks": true,
    "allowed": ["list_directory", "read_file", "glob", ...],
    "shell": {
      "autoApprove": ["git", "npm", "npx"]
    }
  },
  "hooks": {
    "SessionStart": [...],
    "BeforeAgent": [...],
    "SessionEnd": [...]
  }
}
```

### .gk.json

GemKit-specific configuration:

```json
{
  "plan": {
    "namingFormat": "{date}-{issue}-{slug}",
    "dateFormat": "YYMMDD-HHmm"
  },
  "spawn": {
    "defaultModel": "gemini-2.5-flash"
  },
  "notifications": {
    "discord": {
      "enabled": true,
      "notifyMainAgent": true,
      "notifySubAgentRoles": ["code-executor", "git-manager"]
    }
  }
}
```

### .gkignore

Directories blocked from AI access:

```
node_modules
__pycache__
.git
dist
build
```

## Usage Examples

### Spawn an Agent

```bash
# Search for optimal agent-skill combination
gk agent search "implement stripe payment integration"

# Spawn with recommended combination
gk agent spawn -a code-executor -s "backend-development" -p "Implement user API"
```

### Start Coding Workflow

```bash
# Using /code command to execute a plan
/code plans/250113-auth-feature
```

### Research a Topic

```bash
gk agent spawn -a researcher -s research -p "Research JWT best practices 2025"
```

### Run Tests

```bash
# Using /test command
/test

# Or spawn tester agent
gk agent spawn -a tester -s testing -p "Run test suite for auth module"
```

## Discord Notifications

To enable Discord notifications:

1. Create a Discord webhook URL
2. Add to `.gemini/hooks/notifications/.env`:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```
3. Configure in `.gk.json`:
   ```json
   {
     "notifications": {
       "discord": {
         "enabled": true,
         "notifyMainAgent": true,
         "notifySubAgentRoles": ["code-executor"]
       }
     }
   }
   ```

## Environment Variables

Copy `.env.example` to `.gemini/.env` for session state tracking:

```bash
# Auto-managed by hooks
ACTIVE_GK_SESSION_ID=
GK_PROJECT_HASH=
PROJECT_DIR=
ACTIVE_PLAN=
```

## Requirements

- [Gemini CLI](https://github.com/google-gemini/gemini-cli) or compatible AI CLI
- Node.js 18+
- Git (optional, for version control features)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [GemKit Website](https://gemkit.cc)
- [GemKit CLI](https://github.com/therichardngai-code/gemkit-cli)
