---
description: Extract and summarize TLDR newsletter articles from Gmail
argument-hint: <category|"ai","tech","dev","marketing","fintech","infosec","product","design">
---

Extract and summarize a TLDR newsletter. Follow these steps precisely:

## Step 1: Load TLDR Skill & Environment

1. Read the TLDR skill at `${CLAUDE_PLUGIN_ROOT}/skills/tldr-scraper/SKILL.md`.
2. Load environment variables from `${CLAUDE_PLUGIN_ROOT}/.env`:
   ```python
   from dotenv import load_dotenv
   load_dotenv(os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), ".env"))
   ```

## Step 2: Determine Category & Language

The user's argument is: $ARGUMENTS

- If a category is specified (e.g., "ai", "dev"), use it to filter Gmail search.
- If no category, search for the most recent TLDR email and let the user pick, or process the most recent one.
- Determine the output language per the skill's Step 0 rules.

## Step 3: Extract & Summarize

Follow the skill's extraction workflow (Steps 1-4): search Gmail → parse email → fetch all articles in parallel → generate summaries.

## Step 4: Save Locally

Save the assembled Markdown file to the user's workspace:

- Save to: `{workspace}/outputs/tldr-{category}-news-YYYY-MM-DD.md`
- Create the directory if it doesn't exist
- Present the local file path to the user

## Step 5: Launch Subagents

After saving the Markdown file, launch **two subagents in parallel** using the Agent tool. This offloads context-heavy work to fresh context windows, improving output quality.

**IMPORTANT**: Send BOTH Agent tool calls in a **single message** so they run concurrently.

Before launching, prepare the following variables from the work done in Steps 1-4:
- `markdown_path`: the full path to the saved Markdown file
- `view_online_url`: the “View Online” URL extracted from the email
- `newsletter_name`: e.g., “TLDR AI - 2026-03-17”
- `date_str`: e.g., “2026-03-17”
- `category`: e.g., “ai”
- `workspace`: the workspace root path

### Subagent A: `notion-uploader` (background)

Launch with `run_in_background: true`. Prompt:

```
Upload the TLDR newsletter to Notion.

- Markdown file: {markdown_path}
- Newsletter name: {newsletter_name}
- View Online URL: {view_online_url}
```

### Subagent B: `podcast-producer` (foreground)

Launch with `run_in_background: false`. Prompt:

```
Generate a podcast from the TLDR newsletter summary.

- Markdown file: {markdown_path}
- Date: {date_str}
- Category: {category}
- Workspace: {workspace}
- Script output: {workspace}/outputs/tldr-{category}-podcast-{date_str}.txt
- Audio output: {workspace}/outputs/tldr-{category}-podcast-{date_str}.mp3
- TTS script: ${CLAUDE_PLUGIN_ROOT}/scripts/tts_minimax.py
```

### After both agents complete

Present a summary of all outputs:
- Local Markdown file path
- Notion 原始资源 page URL (from notion-uploader)
- Podcast script path and character count (from podcast-producer)
- Notion Podcasts page URL (from podcast-producer)
- Audio file path and size (from podcast-producer)