---
description: Generate a Rednote (小红书) post from a Notion page
argument-hint: <notion-page-url-or-topic>
---

Generate a Rednote (小红书) post. Follow these steps precisely:

## Step 1: Load Rednote Expertise & Environment

1. Read the Rednote skill at `${CLAUDE_PLUGIN_ROOT}/skills/rednote-content/SKILL.md`.
2. Load environment variables from `${CLAUDE_PLUGIN_ROOT}/.env` (contains Cloudflare R2 credentials required for image upload in Step 5):
   ```python
   from dotenv import load_dotenv
   load_dotenv(os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), ".env"))
   ```

## Step 2: Get Source Content

The user's argument is: $ARGUMENTS

- **If it's a Notion URL or page reference**: Use the Notion MCP `notion-fetch` tool (pass the URL as `id`) to read the page content. Extract the source material, any category designation, and any specific instructions.
- **If it's a topic or description**: Use it directly as the content brief.

## Step 3: Determine Category

Based on the source content, determine the most appropriate post category (信息分享 / 产品测评 / 教程/攻略 / 品牌推广). Refer to SKILL.md "Content Categories" for definitions. Default to 信息分享 if ambiguous.

## Step 4: Generate Content Data

Based on the category and source content, generate all text and image data needed for the post. Follow SKILL.md for all content rules and image generation. Output:

1. **标题** (Post Title)
2. **正文** (Body Text)
3. **话题标签** (Hashtags)
4. **封面文字** — short cover text for the cover image
5. **Image page data** — section titles + condensed body for each content page image
6. **Generated images** — cover + content page PNGs

## Step 5: Save Images Locally

If the user has a workspace folder mounted (i.e., the outputs directory is available), copy all generated images to the workspace folder so the user can access them directly:

- Save to: `{workspace}/rednote/{slug}/` (e.g., `cover.png`, `page_01.png`, `page_02.png`, ...)
- Create the directory if it doesn't exist
- Present the local file links to the user using `computer://` URLs

This step runs regardless of R2 upload success — the user always gets a local copy.

## Step 6: Upload Images to R2

Upload all generated images to Cloudflare R2 using `upload_r2.py`:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/upload_r2.py ./output --slug <post_slug>
```

Or programmatically:
```python
import sys, os
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."), "scripts"))
from upload_r2 import upload
results = upload("./output", slug="post-slug")
# results = [{"local": path, "key": r2_key, "url": public_url}, ...]
```

**R2 configuration:**
- Bucket: `notion-data`
- Public URL base: `https://pub-058d0716e3ab466485a24ef35b0c14f1.r2.dev`
- Upload path: `rednote/{slug}/{timestamp}/{filename}`
- Required env vars: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_R2_ACCESS_KEY_ID`, `CLOUDFLARE_R2_SECRET_ACCESS_KEY`

Verify at least one public URL is accessible before proceeding.

## Step 7: Quality Check

Verify the post against the Quality Checklist in SKILL.md. If any item fails, fix it automatically before proceeding.

## Step 8: Save to Notion

Automatically save the post to the 📕 小红书 database (data source ID: `31bb9f47-52ed-8093-b385-000b77cbdf49`):

**Properties:**
- **标题**: Post title without emoji
- **类别**: Content category (e.g., "信息分享")
- **编辑日期**: Today's date (YYYY-MM-DD)

**Page content structure** (use Notion markdown headings for clear sections):

```
![cover](R2_URL/cover.png)

# 标题
{帖子标题}

# 正文
{完整正文 — 包含要点速览、引导语、互动提示等}

# 内容页
## 01 {第一页小标题}
![page_01](R2_URL/page_01.png)

## 02 {第二页小标题}
![page_02](R2_URL/page_02.png)

... (repeat for all content pages)

# 话题标签
{所有 hashtags}
```

All images MUST use R2 public URLs (not local file paths).