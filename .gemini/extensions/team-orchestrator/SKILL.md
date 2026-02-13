---
name: team-orchestrator
description: Use when you need to coordinate multiple AI agents to complete complex tasks in parallel using gk team commands.
license: MIT
version: 2.0.0
updated: 2026-02-13
---

**IMPORTANT:** Inform user when you apply this skill by statement - `team-orchestrator` skill has been applied

# Team Orchestrator

## Overview

Coordinate multiple AI agents working in parallel to complete complex tasks. Use `gk team` commands to create teams, manage tasks, spawn agents, and monitor progress through the **unified central inbox**.

**Core Principles:**
- Agents auto-derive profiles from names (e.g., `researcher-1` → `researcher`)
- Tasks auto-inject into agent messages
- All communication flows through central inbox (`inbox-{teamId}.jsonl`)
- Agents communicate with each other and report progress
- Default model: `gemini-3-flash-preview`

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              CENTRAL INBOX (inbox-{teamId}.jsonl)            │
├──────────────────────────────────────────────────────────────┤
│  WRITES                        READS                         │
│  ├── gk team send              ├── gk team messages          │
│  ├── gk team broadcast         ├── PtyServer (polls @1000ms) │
│  ├── PtyServer (approval_req)  └── gk team respond           │
│  └── task/shutdown messages                                  │
├──────────────────────────────────────────────────────────────┤
│  HOOKS (auto-triggered):                                     │
│  ├── approval_response → Send keystroke to agent PTY         │
│  ├── task_completed → Unblock dependent tasks                │
│  └── shutdown_response → Terminate agent process             │
└──────────────────────────────────────────────────────────────┘
```

## Phase 1: Team Setup

Create team and define tasks with dependencies.

### 1.1 Create Team
```bash
gk team create <team-name> --desc "Description of the project"
```

### 1.2 Create Tasks (Blocking First)
Create independent tasks first, then dependent tasks:
```bash
# Independent tasks (no blockers)
gk team task-create "<subject>" --desc "<detailed description>"

# Dependent task (blocked by others)
gk team task-create "<subject>" --desc "<description>" --blocked-by "task-xxx,task-yyy"
```

**IMPORTANT:** Note task IDs from output for `--blocked-by` references.

## Phase 2: Agent Spawning

Spawn agents with auto-derived profiles using `gk team start`.

### 2.1 Naming Convention
| Name Pattern | Profile Loaded |
|--------------|----------------|
| `researcher-1` | `.gemini/agents/researcher.md` |
| `researcher-2` | `.gemini/agents/researcher.md` |
| `fullstack-developer-1` | `.gemini/agents/fullstack-developer.md` |
| `planner` | `.gemini/agents/planner.md` |

### 2.2 Spawn Commands
```bash
# Basic (profile auto-derived from name)
gk team start --name researcher-1

# With explicit profile
gk team start --name worker-1 -a fullstack-developer

# With additional skills
gk team start --name researcher-1 -s web-search

# With context files
gk team start --name planner -c @plans/

# Spawn in background (use &)
gk team start --name researcher-1 &
gk team start --name researcher-2 &
```

### 2.3 What Happens on Spawn
1. Agent registered in team with allocated port (3377-3476 range)
2. PID stored in team record for kill command
3. PtyServer starts polling central inbox
4. Agent status: `starting` → `ready`

## Phase 3: Task Assignment

Send messages to agents. Tasks are auto-injected.

### 3.1 What Agents Receive Automatically
When you send a message, agents receive:
- Your message content in `<team-message>` block
- Agent context: name, role, team, profile reference
- Current task list: available, in-progress, blocked
- Shell command instructions (task-claim, task-done, send)
- Communication protocol

### 3.2 Send Messages
```bash
# Simple assignment (tasks auto-included)
gk team send researcher-1 "Start working on available research tasks"

# Specific task assignment
gk team send researcher-1 "Claim task-xxx and complete the security research"

# Broadcast to all agents
gk team broadcast "Status update: Phase 1 complete"
```

## Phase 4: Monitoring & Approval

Track progress through central inbox and approve tool usage.

### 4.1 View Central Inbox
```bash
# View all messages
gk team messages

# View pending items only
gk team messages --pending

# Filter by type
gk team messages --type approval_request
gk team messages --type message
gk team messages --type broadcast

# Filter by sender/recipient
gk team messages --from researcher-1
gk team messages --to leader

# Combine filters
gk team messages --pending --type approval_request

# JSON output
gk team messages --json
```

### 4.2 Approve Tool Requests
When agents need to run shell commands, they generate approval requests.

```bash
# Approve single request by message ID
gk team respond <messageId> --approve

# Reject with reason
gk team respond <messageId> --reject "Use a different approach"

# Approve ALL pending requests (recommended for automation)
gk team respond --approve-all
```

### 4.3 Monitor Task Progress
```bash
# Task status overview
gk team tasks

# Check agent structured output
gk team exchange researcher-1

# Read raw agent output
gk team read researcher-1
```

### 4.4 Approval Loop Pattern
```bash
# Continuous approval loop
while true; do
  gk team respond --approve-all 2>/dev/null
  sleep 5
done
```

## Phase 5: Cleanup

Gracefully shutdown and cleanup when work is complete.

### 5.1 Graceful Shutdown
```bash
# Check all tasks are complete
gk team tasks

# Verify deliverables created
ls -la plans/

# Emergency shutdown all agents (kills processes)
gk team kill
```

### 5.2 Full Reset (Clean Slate)
```bash
# Delete all team data (teams, tasks, messages, ports)
gk team reset
```

### 5.3 Cleanup Stale Resources
```bash
# Clean up orphaned processes and stale ports
gk team cleanup

# Check port allocations
gk team ports
```

**IMPORTANT:** Always run `gk team tasks` before cleanup to verify all work is complete.

## Command Reference

### Team Management
| Command | Description |
|---------|-------------|
| `gk team create <name> --desc "..."` | Create new team |
| `gk team list` | List all teams |
| `gk team info [teamId]` | Show team details and members |
| `gk team kill [teamId]` | Emergency shutdown (force kill processes) |
| `gk team cleanup` | Clean up orphaned processes and stale ports |
| `gk team ports` | Show port allocations |
| `gk team reset` | Delete all team data (full reset) |

### Task Management
| Command | Description |
|---------|-------------|
| `gk team task-create "<subject>" --desc "..."` | Create task |
| `gk team task-create "<subject>" --blocked-by "id1,id2"` | Create dependent task |
| `gk team task-claim <taskId> --as <agentName>` | Claim task for agent |
| `gk team task-done <taskId>` | Mark task completed |
| `gk team tasks [teamId]` | List all tasks with status |

### Agent Spawning
| Command | Description |
|---------|-------------|
| `gk team start --name <name>` | Spawn (profile auto-derived) |
| `gk team start --name <name> -a <profile>` | Spawn with explicit profile |
| `gk team start --name <name> -s <skills>` | Spawn with additional skills |
| `gk team start --name <name> -c <context>` | Spawn with context files |
| `gk team start --name <name> --cli claude` | Use Claude CLI instead of Gemini |

### Messaging (Central Inbox)
| Command | Description |
|---------|-------------|
| `gk team send <agent> "<message>"` | Send direct message |
| `gk team broadcast "<message>"` | Send to all agents |
| `gk team messages` | View central inbox |
| `gk team messages --pending` | View pending items |
| `gk team messages --type <type>` | Filter by message type |
| `gk team respond <msgId> --approve` | Approve request |
| `gk team respond <msgId> --reject "reason"` | Reject request |
| `gk team respond --approve-all` | Approve all pending |

### Agent Interaction
| Command | Description |
|---------|-------------|
| `gk team exchange <agent>` | Get structured JSON output |
| `gk team read <agent>` | Read raw terminal output (last 200 lines) |

## Message Types

| Type | Icon | Description |
|------|------|-------------|
| `message` | 💬 | Direct message between agents |
| `broadcast` | 📢 | Leader → all members |
| `approval_request` | 🔔 | Agent needs tool approval |
| `approval_response` | ✓ | Leader approved/rejected |
| `plan_approval_request` | 📋 | Agent requests plan approval |
| `plan_approval_response` | ✅ | Leader approves/rejects plan |
| `task_created` | 📋 | New task created |
| `task_claimed` | 🏃 | Task claimed by agent |
| `task_completed` | 🎉 | Task marked done (triggers unblock) |
| `status_update` | 📊 | Agent status change |
| `shutdown_request` | 🔴 | Leader requests shutdown |
| `shutdown_response` | 🟢 | Agent responds to shutdown |

## Agent Communication Protocol

Agents are instructed to:
1. Claim tasks using: `gk team task-claim <taskId> --as <agentName>`
2. Complete tasks using: `gk team task-done <taskId>`
3. Send messages using: `gk team send <recipient> "<message>"`
4. Notify Main Agent (leader) when tasks complete
5. Notify blocked agents when unblocking them

## Example: Bug Fixing with Two Developers

```bash
# === Phase 1: Setup ===
gk team reset
gk team create debug-team --desc "Fix authentication bugs"

# Create tasks
gk team task-create "Analyze bugs" --desc "Read src/buggy-auth.ts and identify all bugs"
gk team task-create "Fix bugs" --desc "Implement fixes for identified bugs"

# === Phase 2: Spawn Agents ===
gk team start --name dev-1 -a fullstack-developer &
gk team start --name dev-2 -a fullstack-developer &

# Wait for initialization
sleep 60

# Verify agents ready
gk team info

# === Phase 3: Assign Work ===
gk team send dev-1 "You are the lead. Claim 'Analyze bugs' task, read src/buggy-auth.ts, identify all bugs, coordinate with dev-2."
gk team send dev-2 "You are support. Help dev-1 analyze, then claim 'Fix bugs' task when ready."

# === Phase 4: Monitor & Approve ===
# View pending approvals
gk team messages --pending --type approval_request

# Approve all (run multiple times)
gk team respond --approve-all

# Check progress
gk team tasks
gk team exchange dev-1
gk team exchange dev-2

# === Phase 5: Cleanup ===
gk team tasks  # Verify completion
gk team kill   # Shutdown agents
gk team reset  # Clean slate
```

## Example: Research Team with Dependencies

```bash
# Clean slate
gk team reset

# Create team
gk team create research-project --desc "Multi-topic Research"

# Create independent research tasks
gk team task-create "Research Frontend" --desc "Investigate React/Next.js patterns"
gk team task-create "Research Backend" --desc "Investigate Node.js frameworks"
gk team task-create "Research Security" --desc "Investigate auth best practices"

# Note task IDs (e.g., task-aaa, task-bbb, task-ccc)

# Create dependent synthesis task
gk team task-create "Create Master Plan" --desc "Synthesize all research into implementation plan" --blocked-by "task-aaa,task-bbb,task-ccc"

# Spawn researchers
gk team start --name researcher-1 &
gk team start --name researcher-2 &
gk team start --name researcher-3 &
gk team start --name planner &

sleep 60

# Assign work
gk team send researcher-1 "Claim and complete Frontend research"
gk team send researcher-2 "Claim and complete Backend research"
gk team send researcher-3 "Claim and complete Security research"
gk team send planner "Wait for all research, then create Master Plan"

# Approval loop
for i in $(seq 1 30); do
  gk team respond --approve-all 2>/dev/null
  gk team tasks
  sleep 10
done

# Cleanup
gk team kill
gk team reset
```

## Quality Standards

Ensure coordination meets these criteria:
- **Clear Tasks**: Each task has specific, actionable description
- **Proper Dependencies**: Blocking tasks created before dependent tasks
- **Role Matching**: Agent names match available profiles
- **Progress Tracking**: Regular `gk team tasks` checks
- **Prompt Approval**: Use `gk team respond --approve-all` for automation
- **Clean Shutdown**: Always `gk team kill` before `gk team reset`

## Troubleshooting

### Agents show wrong context
Old processes may be holding ports. Fix:
```bash
gk team kill
gk team cleanup
# Or use PowerShell to force kill specific PIDs
powershell -Command "Stop-Process -Id <PID> -Force"
```

### Kill command shows "killed 0"
PIDs not stored correctly (legacy issue, now fixed). Verify:
```bash
gk team info --json | grep '"pid"'
```

### Approval requests not appearing
Check if agent has pending tools:
```bash
gk team exchange <agentName>
# Look for "pending" array in output
```

### Agent not receiving messages
Verify agent status is "ready":
```bash
gk team info
```

## Special Considerations

- **Parallel Spawning**: Use `&` to spawn multiple agents simultaneously
- **Initialization Time**: Wait 30-60 seconds after spawning before sending messages
- **Tool Approval**: Gemini CLI requires confirmation; use `--approve-all` for automation
- **Task IDs**: Note IDs when creating tasks for `--blocked-by` references
- **Agent Names**: Follow `role-N` pattern for auto-profile loading
- **Port Range**: Agents use ports 3377-3476 (max 100 concurrent agents)
- **Default Model**: `gemini-3-flash-preview` (configurable via `gk config set spawn.defaultModel`)

## Output Requirements

When orchestrating a team:
1. Document team structure and task dependencies
2. Log task completion status
3. Collect agent outputs using `gk team exchange`
4. Verify all deliverables created by agents
5. Clean up with `gk team kill` and `gk team reset`

**IMPORTANT:** Create blocking tasks BEFORE dependent tasks.
**IMPORTANT:** Wait for agent initialization before sending messages.
**IMPORTANT:** Use `gk team respond --approve-all` for continuous approval.
