---
description: Extract and summarize AI Today newsletter articles from Gmail
argument-hint: <category|"ai","tech","dev","marketing","fintech","infosec","product","design">
---

Extract and summarize an AI Today newsletter. **Always produce both Chinese and English versions** of all outputs. Follow these steps precisely:

## Step 1: Load TLDR Skill & Environment

- Read the TLDR skill at `${CLAUDE_PLUGIN_ROOT}/skills/tldr-scraper/SKILL.md`.

## Step 2: Determine Category

The user's argument is: $ARGUMENTS

- If a category is specified (e.g., “ai”, “dev”), use it to filter Gmail search.
- If no category, search for the most recent TLDR email and let the user pick, or process the most recent one.
- The skill's Step 0 will produce both Chinese and English outputs.

## Step 3: Extract & Summarize (Bilingual)

Follow the skill's extraction workflow (Steps 1-3): search Gmail → parse email → fetch articles sequentially.

For **Step 4 (Generate Summaries)**, generate summaries in **both Chinese and English** for every article. Each article should have:
- A Chinese short summary + Chinese detailed summary
- An English short summary + English detailed summary

Then assemble **two separate Markdown files** using the skill's Step 5 template:
- **Chinese version**: Use Chinese section headers, Chinese summaries, Chinese footer (per the skill's Chinese column in the mapping table)
- **English version**: Use English section headers, English summaries, English footer (per the skill's English column in the mapping table)

## Step 4: Save Locally

Save **both** Markdown files to the user's workspace:

- Chinese: `{workspace}/outputs/ai-today-{category}-news-YYYY-MM-DD-cn.md`
- English: `{workspace}/outputs/ai-today-{category}-news-YYYY-MM-DD-en.md`
- Create the directory if it doesn't exist
- Present both local file paths to the user

## Step 5: Launch Subagents

After saving both Markdown files, launch **four subagents** using the Agent tool. This offloads context-heavy work to fresh context windows.

**IMPORTANT**: Send ALL four Agent tool calls in a **single message** so they run concurrently.

Before launching, prepare the following variables from the work done in Steps 1-4:
- `cn_markdown_path`: full path to the Chinese Markdown file
- `en_markdown_path`: full path to the English Markdown file
- `view_online_url`: the “View Online” URL extracted from the email
- `newsletter_name`: e.g., “AI Today - 2026-03-17”
- `date_str`: e.g., “2026-03-17”
- `category`: e.g., “ai”
- `workspace`: the workspace root path

### Subagent A: `notion-uploader` — Chinese (background)

Launch with `run_in_background: true`. Prompt:

```
Upload the AI Today newsletter (Chinese version) to Notion.

- Markdown file: {cn_markdown_path}
- Newsletter name: {newsletter_name} CN
- View Online URL: {view_online_url}
```

### Subagent B: `notion-uploader` — English (background)

Launch with `run_in_background: true`. Prompt:

```
Upload the AI Today newsletter (English version) to Notion.

- Markdown file: {en_markdown_path}
- Newsletter name: {newsletter_name} EN
- View Online URL: {view_online_url}
```

### Subagent C: `podcast-producer` — Chinese (foreground)

Launch with `run_in_background: false`. Prompt:

```
Generate a Chinese podcast from the AI Today newsletter summary.

- Markdown file: {cn_markdown_path}
- Date: {date_str}
- Category: {category}
- Workspace: {workspace}
- Language: Chinese
- Script output: {workspace}/outputs/ai-today-{category}-podcast-{date_str}-cn.txt
- Audio output: {workspace}/outputs/ai-today-{category}-podcast-{date_str}-cn.mp3
- TTS script: ${CLAUDE_PLUGIN_ROOT}/scripts/tts_minimax.py
```

### Subagent D: `podcast-producer` — English (foreground)

Launch with `run_in_background: false`. Prompt:

```
Generate an English podcast from the AI Today newsletter summary.

- Markdown file: {en_markdown_path}
- Date: {date_str}
- Category: {category}
- Workspace: {workspace}
- Language: English
- Script output: {workspace}/outputs/ai-today-{category}-podcast-{date_str}-en.txt
- Audio output: {workspace}/outputs/ai-today-{category}-podcast-{date_str}-en.mp3
- TTS script: ${CLAUDE_PLUGIN_ROOT}/scripts/tts_minimax.py
```

### After all agents complete

Present a summary of all outputs:
- Local Markdown file paths (CN + EN)
- Notion “AI资讯速递” page URLs (CN + EN, from notion-uploaders)
- Podcast script paths and character/word counts (CN + EN, from podcast-producers)
- Notion Podcasts page URLs (CN + EN, from podcast-producers)
- Audio file paths and sizes (CN + EN, from podcast-producers)