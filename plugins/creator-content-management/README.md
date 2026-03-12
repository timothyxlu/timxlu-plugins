# Content Management

Create platform-optimized social media content, podcasts and video content, manage content workflows, and save to Notion.

## Supported Platforms

- **Rednote (小红书)** — full content creation with translation, formatting, and platform-native style
- **TLDR Newsletter** — extract and summarize tech news from TLDR newsletters via Gmail

More platforms can be added as additional skills.

## Components

| Type | Name | Description |
|------|------|-------------|
| Skill | rednote-content | Rednote (小红书) platform expertise — formatting, hashtags, writing style, category templates |
| Skill | tldr-scraper | TLDR newsletter extraction — Gmail parsing, article fetching, bilingual summaries |
| Command | `/rednote` | Generate a complete Rednote post from a Notion page or topic |
| Command | `/tldr` | Extract and summarize a TLDR newsletter from Gmail, save to Notion |

## Usage

### /rednote

```
/rednote <notion-page-url-or-topic>
```

Reads your source content, detects the category (信息分享, 产品测评, 教程/攻略, or 品牌推广), generates a complete post with cover text, title, body, and hashtags, then saves the result back to Notion.

**Examples:**
- `/rednote https://www.notion.so/my-page-123` — read from Notion, generate post, save back
- `/rednote AI productivity tools review` — generate a post from a topic

### /tldr

```
/tldr <category>
```

Searches Gmail for the latest TLDR newsletter, fetches all original articles, generates short + detailed summaries, and saves the digest locally and to Notion.

**Examples:**
- `/tldr ai` — extract the latest TLDR AI newsletter
- `/tldr dev` — extract the latest TLDR Dev newsletter
- `/tldr` — extract the most recent TLDR newsletter (any category)

### Skills (automatic)

Skills activate automatically when you mention relevant topics — e.g., creating 小红书 content or extracting TLDR newsletters — even without a slash command.

## Setup

Requires the following connectors in Cowork:
- **Notion** — for reading source content and saving posts/digests
- **Gmail** — for extracting TLDR newsletters (required by `/tldr`)
