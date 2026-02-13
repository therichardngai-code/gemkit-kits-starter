---
name: spawn-agent
description: Delegate tasks to Gemini sub-agents with intelligent BM25 search for optimal agent-skill combinations. Supports both one-shot spawn and interactive session modes.
license: MIT
version: 2.1.0
updated: 2026-02-13
---

**IMPORTANT:** Inform user when you apply this skill by statement - `spawn-agent` skill has been applied

# Spawn Gemini Agents

Delegate tasks to specialized Gemini sub-agents with intelligent search for optimal agent-skill combinations.

**Two Modes:**
- **One-Shot Mode**: `gk agent spawn` - Fire and forget, waits for completion
- **Interactive Mode**: `gk agent start/send/stop` - Persistent session with multiple exchanges

```
+------------------+
|  Gemini (You)    |  Main coordinator
+--------+---------+
         |
    +----+----+
    |         |
    v         v
  spawn    start (interactive)
    |         |
    v         v
 [One-Shot] [Session: send/wait/exchange/stop]
```

## Quick Start

### One-Shot Mode (Fire & Forget)
```bash
# Search for best agent-skill combination
gk agent search "implement stripe payment integration"

# Spawn with recommended combination
gk agent spawn -a code-executor -s "payment-integration,backend-development" -p "Implement Stripe checkout"
```

### Interactive Mode (Persistent Session)
```bash
# Start a session
gk agent start -a researcher -s research

# Send prompts (can send multiple)
gk agent send "Research JWT best practices"
gk agent wait

# Check for tool approvals
gk agent pending
gk agent send "1"  # Approve tool

# Get structured output
gk agent exchange

# Stop when done
gk agent stop
```

## CLI Commands

### Search for Optimal Combination

```bash
gk agent search "<task description>"
```

Returns ranked results with:
- **Agent**: Best agent for the task
- **Skills**: Optimal skill combination
- **Score**: BM25 relevance score
- **Suggested command**: Ready-to-use spawn command

### Spawn Agent (One-Shot)

```bash
gk agent spawn [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--prompt` | `-p` | Task for sub-agent (required) |
| `--agent` | `-a` | Agent profile name |
| `--skills` | `-s` | Comma-separated skills |
| `--context` | `-c` | Context files (@file syntax) |
| `--model` | `-m` | Model override |
| `--tools` | `-t` | Comma-separated tools to auto-approve |
| `--cli` | | CLI provider: `gemini` (default) or `claude` |
| `--music` | | Enable elevator music |
| `--no-music` | | Disable elevator music |

### List Agents

```bash
gk agent list
```

### Agent Info

```bash
gk agent info <agent-name>
```

## Interactive Mode

Start a persistent AI session for multi-turn conversations with tool approval control.

### Session Commands

| Command | Description |
|---------|-------------|
| `gk agent start [options]` | Start interactive session |
| `gk agent send "<prompt>"` | Send prompt to session |
| `gk agent wait [timeout]` | Wait for completion (default: 120s) |
| `gk agent pending` | Check pending tool confirmations |
| `gk agent exchange` | Get structured JSON output |
| `gk agent read [lines]` | Read raw terminal output (default: 200 lines) |
| `gk agent status` | Check session status |
| `gk agent stop` | Stop session (force kills process) |

### Start Options

```bash
gk agent start [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--agent` | `-a` | Agent profile name |
| `--skills` | `-s` | Comma-separated skills |
| `--context` | `-c` | Context files (@file syntax) |
| `--model` | `-m` | Model override |
| `--tools` | `-t` | Comma-separated tools to allow |
| `--cli` | | CLI provider: `gemini` (default) or `claude` |

### Interactive Workflow

```
┌─────────────┐
│  gk agent   │
│   start     │ ──► Session starts on port 3377
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  gk agent   │
│   send      │ ──► Send prompt to AI
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  gk agent   │ ──► │  Tool       │
│   wait      │     │  Pending?   │
└──────┬──────┘     └──────┬──────┘
       │                   │ Yes
       │ Complete          ▼
       │           ┌─────────────┐
       │           │  gk agent   │
       │           │  pending    │ ──► View tool details
       │           └──────┬──────┘
       │                   │
       │                   ▼
       │           ┌─────────────┐
       │           │  gk agent   │
       │           │  send "1"   │ ──► Approve tool (1=once, 2=session)
       │           └──────┬──────┘
       │                   │
       ▼                   ▼
┌─────────────┐
│  gk agent   │
│  exchange   │ ──► Get structured output (JSON)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  gk agent   │
│   stop      │ ──► Kill process & cleanup
└─────────────┘
```

### Tool Approval

When the AI requests to use tools (file write, shell command, etc.), you need to approve:

```bash
# Check what's pending
gk agent pending

# Output shows options:
# {
#   "hasPending": true,
#   "tools": [{ "type": "write_file", "path": "...", "options": ["1. Allow once", "2. Allow for this session", "3. No"] }]
# }

# Approve once
gk agent send "1"

# Approve for session (recommended for multiple operations)
gk agent send "2"

# Reject
gk agent send "3"
```

### Exchange Output

Get structured JSON response:

```bash
gk agent exchange
```

Returns:
```json
{
  "id": "exchange-uuid",
  "timestamp": "2026-02-13T...",
  "prompt": "your prompt",
  "answer": "AI response text",
  "pending": [],
  "toolResults": [
    { "type": "write_file", "detail": "path/to/file.md", "status": "completed" }
  ],
  "status": "complete"
}
```

### Interactive Examples

#### Code Review Session
```bash
# Start session
gk agent start --cli gemini

# Send review request
gk agent send "Review src/auth.ts for security issues and create a report at docs/review.md"
gk agent wait 180

# Approve file write
gk agent pending
gk agent send "2"
gk agent wait

# Get result
gk agent exchange

# Stop
gk agent stop
```

#### Research Session with Multiple Prompts
```bash
# Start with researcher profile
gk agent start -a researcher -s research

# First research task
gk agent send "Research React 19 new features"
gk agent wait
gk agent exchange

# Follow-up question (same session)
gk agent send "How does the new compiler compare to Vue's approach?"
gk agent wait
gk agent exchange

# Stop when done
gk agent stop
```

#### Using Claude CLI
```bash
# Start with Claude instead of Gemini
gk agent start --cli claude -a code-executor

gk agent send "Implement a rate limiter middleware"
gk agent wait

gk agent stop
```

## When to Use Each Mode

| Use Case | Mode | Reason |
|----------|------|--------|
| Single task, fire & forget | `spawn` | Simpler, blocks until done |
| Multiple related prompts | `start/send` | Maintains context between prompts |
| Need to approve tools manually | `start/send` | Full control over tool execution |
| Long-running with progress check | `start/send` | Can check status, read output |
| Automated scripting | `spawn` | Single command, exit code |
| Exploratory/debugging | `start/send` | Interactive, can adjust approach |

## Search Engine

The search uses **BM25 algorithm** with:

### Intent Detection

Automatically detects task intent from keywords:

| Intent | Keywords | Agent |
|--------|----------|-------|
| `research` | research, investigate, explore, analyze | `researcher` |
| `plan` | plan, design, architecture, roadmap | `planner` |
| `execute` | implement, build, create, add | `code-executor` |
| `debug` | debug, fix, troubleshoot, error | `debugger` |
| `review` | review, audit, assess | `code-reviewer` |
| `test` | test, verify, validate | `tester` |
| `design` | beautiful, stunning, ui design | `ui-ux-designer` |
| `docs` | document, write docs | `docs-manager` |
| `git` | commit, push, merge, branch | `git-manager` |

### Domain Detection

Identifies technology domain:

| Domain | Keywords |
|--------|----------|
| `frontend` | react, vue, tailwind, component |
| `backend` | api, endpoint, server, middleware |
| `auth` | login, oauth, authentication, jwt |
| `payment` | stripe, checkout, billing, subscription |
| `database` | prisma, postgresql, query, migration |
| `mobile` | react native, flutter, ios, android |
| `fullstack` | next.js, nuxt, sveltekit |
| `ecommerce` | shopify, cart, checkout |
| `ai` | llm, openai, chatbot, embedding |
| `media` | image, video, upload, ocr |

### Complexity Detection

Determines skill count based on keywords:

| Complexity | Keywords | Max Skills |
|------------|----------|------------|
| `simple` | quick, simple, basic | 1 |
| `standard` | (default) | 2 |
| `full` | comprehensive, complete, thorough | 3 |
| `complex` | enterprise, advanced, sophisticated | 5 |

### Synonym Expansion

Query terms are expanded using synonyms for better matching:
- "build" -> build, create, implement, develop
- "fix" -> fix, debug, repair, troubleshoot
- "check" -> check, review, audit, verify

## Examples

### Research Tasks

```bash
# Simple research
gk agent spawn -a researcher -s research -p "Research JWT best practices"

# Deep codebase analysis
gk agent spawn -a researcher -s "repomix,research" -p "Analyze project architecture"

# Backend research
gk agent spawn -a researcher -s "research,backend-development" -p "Research API design patterns"
```

### Implementation Tasks

```bash
# Backend API
gk agent spawn -a code-executor -s backend-development -p "Implement user registration API"

# Payment integration
gk agent spawn -a code-executor -s "payment-integration,backend-development" -p "Implement Stripe checkout"

# Beautiful UI
gk agent spawn -a code-executor -s "frontend-design,ui-ux-pro-max" -p "Create stunning pricing page"

# Fullstack auth
gk agent spawn -a code-executor -s "backend-development,better-auth,web-frameworks" -p "Implement OAuth login"
```

### Debugging Tasks

```bash
# General debugging
gk agent spawn -a debugger -s debugging -p "Fix login error"

# Database issues
gk agent spawn -a debugger -s "debugging,databases" -p "Debug slow query performance"

# Next.js errors
gk agent spawn -a debugger -s "debugging,web-frameworks" -p "Fix hydration mismatch error"
```

### Design Tasks

```bash
# UI design
gk agent spawn -a ui-ux-designer -s "ui-ux-pro-max,frontend-design" -p "Design user dashboard"

# Mobile design
gk agent spawn -a ui-ux-designer -s "mobile-development,ui-ux-pro-max" -p "Design mobile app navigation"
```

## Available Agents

| Agent | Purpose | Default Skills |
|-------|---------|----------------|
| `researcher` | Research, investigation, analysis | `research` |
| `planner` | Architecture, planning, roadmaps | `planning` |
| `code-executor` | Implementation, development | varies by domain |
| `debugger` | Bug fixing, troubleshooting | `debugging` |
| `tester` | Testing, validation | `testing` |
| `code-reviewer` | Code review, security audit | `code-review` |
| `ui-ux-designer` | UI/UX design | `frontend-design` |
| `docs-manager` | Documentation | `planning` |
| `git-manager` | Git operations | `planning` |

## Data Files

Search data stored in `.gemini/extensions/spawn-agent/data/`:

| File | Purpose |
|------|---------|
| `combinations.csv` | Agent-skill combinations with keywords |
| `intents.csv` | Intent keywords and mappings |
| `domains.csv` | Domain keywords and skills |
| `synonyms.csv` | Query expansion synonyms |

## Elevator Music

Enable for long-running tasks:

```bash
# Enable for single spawn
gk agent spawn -a researcher -p "Deep research task" --music

# Configure default
gk config set spawn.music true
```

## Configuration

In `.gemini/.gk.json`:

```json
{
  "spawn": {
    "defaultModel": "gemini-3-flash-preview",
    "music": false,
    "musicFile": null
  }
}
```

## Technical Details

### Interactive Session
- **Port**: 3377 (fixed for single-agent mode)
- **Session file**: `~/.gk-pty-session.json`
- **Process**: Background Node.js server with PTY
- **Stop behavior**: Sends graceful stop, then force kills PID after 2s

### One-Shot Spawn
- **Process**: Direct child process, blocks until completion
- **Output**: Streams to stdout/stderr
- **Exit code**: Propagated from sub-agent

## Troubleshooting

### Session won't stop
```bash
# Force stop
gk agent stop

# If still running, check process
netstat -ano | grep 3377
taskkill /F /PID <pid>   # Windows
kill -9 <pid>            # Unix
```

### Port already in use
```bash
# Check what's using port 3377
netstat -ano | grep 3377

# Clean up stale session
rm ~/.gk-pty-session.json
```

### Agent not found
```bash
# List available agents
gk agent list

# Check agent folders
ls .gemini/agents/
ls .claude/agents/
```

## References

- `./references/agent-skill-combinations.md` - Full combination guide
- `./data/combinations.csv` - Searchable combinations database
