---
name: todoist-quick-add
description: >
  Quickly add or complete subtasks in Todoist using a simple command syntax. Trigger this skill whenever the user says "/todoist" — even just the bare word "/todoist" with no other context. Also trigger on natural phrasing like "add X to my Todoist", "put X under Y in Todoist", "todoist: add X to #Y", "add X to #Family", "completed X from #Family", "remove X from #Family", "done with X on #Acute", "delete X from #Church", or any request that involves adding, completing, or removing a task or subtask in Todoist. If the user references a #ParentName and wants to add or complete something under it, this is the skill. Even if the user just says "/todoist add lightbulbs to #Family" or "/todoist completed lightbulbs from #Family" with no other explanation, use this skill.
---

# Todoist Quick Add & Complete

Add subtasks under parent tasks or mark them complete in Todoist using a short command or natural language. Supports due dates, priorities, labels, file attachments, and batch operations — all optional.

## Detect the Action

First, determine whether the user wants to **add** or **complete** a task. The signal words are:

| Action | Trigger words |
|--------|--------------|
| **Add** | "add", "put", "create", "new", default if ambiguous |
| **Complete** | "completed", "complete", "done", "finished", "remove", "delete", "check off", "mark done" |

Then follow the corresponding section below.

## Command Syntax

### Adding tasks

```
/todoist add [task] to #[Parent]
```

Examples — all equivalent:

- `/todoist add Snow blower to #Family`
- `/todoist add Snow blower to #Family due tomorrow p2`
- `Add snow blower to #Family in Todoist`
- `Put "call electrician" under #Carlsbad`
- `/todoist add Task A, Task B, Task C to #Family`
- `/todoist add Task A to #Family, Task B to #Acute, Task C to #Church`

### Completing tasks

```
/todoist completed [task] from #[Parent]
```

Examples — all equivalent:

- `/todoist completed Snow blower from #Family`
- `/todoist done Snow blower from #Family`
- `Remove snow blower from #Family`
- `Mark "call electrician" done under #Carlsbad`
- `/todoist completed Task A, Task B from #Family`
- `/todoist completed Task A from #Family, Task B from #Acute`

## Parsing the Request

Extract the following from the user's message. If a field isn't mentioned, ignore it — don't prompt for it.

| Field | How to detect | Required |
|-------|--------------|----------|
| Task name(s) | The thing being added | Yes |
| Parent task | After "to #" or "under #" or "under" — the `#` prefix is a convention, not literal Todoist syntax | Yes |
| Due date | "due [date]", "by [date]", "tomorrow", "next Monday", etc. | No |
| Priority | "p1", "p2", "p3", "p4" anywhere in the command | No |
| Labels | "@label" pattern | No |
| Attachment | A file attached to the user's message in the conversation | No |

### Multiple tasks

The user can specify multiple tasks in two ways (works for both adding and completing):

1. **Same parent:** Comma-separated task names before a single `#Parent`
   - `/todoist add Mow lawn, Fix fence, Clean gutters to #Family`
   - `/todoist completed Mow lawn, Fix fence from #Family`

2. **Different parents:** Comma-separated `task to/from #Parent` pairs
   - `/todoist add Mow lawn to #Family, Review APA to #Acute, Prep lesson to #Church`
   - `/todoist completed Mow lawn from #Family, Review APA from #Acute`

Parse carefully. The distinguishing signal is whether `#Parent` appears once (all tasks share it) or multiple times (each task has its own parent).

## Execution Steps — Adding Tasks

### Step 1 — Find the parent task(s)

For each unique parent name the user referenced, search across ALL projects (not just Inbox):

```
Todoist:find-tasks with searchText = "[Parent name]"
```

The parent tasks in Ryan's system use a `# ` prefix in their Todoist content (e.g., `# Family`, `# Acute`). Match on the core name, ignoring the `#` and any leading/trailing whitespace.

**If no match is found:** Tell the user you couldn't find a parent task matching that name. List the search results (if any) so they can clarify. Do not create a new parent task without explicit confirmation.

**If multiple matches are found:** Pick the one whose content is exactly `# [Name]` (the header-style parent). If still ambiguous, ask the user to clarify.

### Step 2 — Add the subtask(s)

Call `Todoist:add-tasks` with an array of task objects. For each task:

- `content`: The task name
- `parentId`: The ID of the matched parent task
- Only include `dueString`, `priority`, or `labels` if the user specified them

Example single task:
```json
[{"content": "Snow blower", "parentId": "abc123"}]
```

Example batch (same parent):
```json
[
  {"content": "Mow lawn", "parentId": "abc123"},
  {"content": "Fix fence", "parentId": "abc123"},
  {"content": "Clean gutters", "parentId": "abc123"}
]
```

Example batch (different parents):
```json
[
  {"content": "Mow lawn", "parentId": "abc123"},
  {"content": "Review APA", "parentId": "def456"},
  {"content": "Prep lesson", "parentId": "ghi789"}
]
```

### Step 3 — Attach files (if applicable)

If the user's message includes an attached file, add a comment to each newly created subtask with the file content or a reference to it:

```
Todoist:add-comments with taskId = [new task ID], content = [file content or description]
```

Since Todoist comments support Markdown, format the file content cleanly. If the file is too large for a comment, summarize it and note that the full file is available in the conversation.

### Step 4 — Confirm

Report back with a concise confirmation. No unnecessary chatter. Format:

```
Added to #Family:
- Snow blower (due tomorrow, p2)

Added to #Acute:
- Review APA draft
```

If anything failed, say what and why.

---

## Execution Steps — Completing Tasks

### Step 1 — Find the parent task(s)

Same as the Add flow — search across all projects for the parent:

```
Todoist:find-tasks with searchText = "[Parent name]"
```

Match on the `# [Name]` header-style parent. Same disambiguation rules apply.

### Step 2 — Find the subtask(s) to complete

Once you have the parent task ID, search for the subtask(s) the user named:

```
Todoist:find-tasks with parentId = "[parent task ID]", searchText = "[subtask name]"
```

**If no match is found:** Tell the user you couldn't find a subtask matching that name under the specified parent. List the existing subtasks so they can clarify or correct a typo.

**If multiple matches are found:** If one is an exact match, use it. If ambiguous, list the candidates and ask the user to pick.

### Step 3 — Complete the subtask(s)

Call `Todoist:complete-tasks` with the IDs of the matched subtasks:

```
Todoist:complete-tasks with ids = ["task_id_1", "task_id_2"]
```

This marks them as completed — it does not delete them. They'll appear in Todoist's completed tasks history.

### Step 4 — Confirm

Report back concisely:

```
Completed from #Family:
- Snow blower ✓
- Fix fence ✓
```

If any task couldn't be found or completed, say what and why.

## Important Notes

- Ryan doesn't code — don't show raw API responses or JSON. Just confirm what was added.
- Don't ask for missing optional fields. If the user didn't specify a due date, priority, or label, just skip them.
- The `#` in the user's command is a human-readable convention to signal "parent task." It maps to the `# Family` style header tasks in Ryan's Todoist Inbox structure, but also search across all projects.
- Always search broadly first. Ryan's parent tasks are currently in Inbox, but this could change.
- If the Todoist MCP tools aren't loaded yet, use `tool_search` to load them before proceeding.
