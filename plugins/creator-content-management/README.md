# Content Management

Create platform-optimized social media content, podcasts and video content, manage content workflows, and save to Notion.

## Supported Platforms

- **Rednote (小红书)** — full content creation with translation, formatting, and platform-native style

More platforms can be added as additional skills.

## Components

| Type | Name | Description |
|------|------|-------------|
| Skill | rednote-content | Rednote (小红书) platform expertise — formatting, hashtags, writing style, category templates |
| Command | `/rednote` | Generate a complete Rednote post from a Notion page or topic |

## Usage

### /rednote

```
/rednote <notion-page-url-or-topic>
```

Reads your source content, detects the category (信息分享, 产品测评, 教程/攻略, or 品牌推广), generates a complete post with cover text, title, body, and hashtags, then saves the result back to Notion.

**Examples:**
- `/rednote https://www.notion.so/my-page-123` — read from Notion, generate post, save back
- `/rednote AI productivity tools review` — generate a post from a topic

### Rednote skill (automatic)

The skill activates automatically when you mention creating 小红书 content, even without the `/rednote` command.

## Setup

Requires the Notion connector to be connected in Cowork for reading and saving content. No additional API keys needed.
