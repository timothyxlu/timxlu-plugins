---
name: tldr-scraper
description: Extract TLDR newsletter articles from Gmail, fetch originals, and generate bilingual summaries in Markdown.
---
 
# TLDR Newsletter Scraper (Gmail-based)
 
A skill for extracting tech news from TLDR newsletters **via Gmail** and converting them into well-structured Markdown files with categorized links and **AI-generated summaries** for each article.
 
## Overview
 
This skill enables Claude to:
1. **Search Gmail** for the latest TLDR newsletter email (from `dan@tldrnewsletter.com`)
2. **Read the full email body** and parse all article sections
3. Extract article titles, URLs, categories, read times, and TLDR's own blurbs
4. **Fetch each article's original content** via `stealth-browser-mcp`
5. **Generate a short summary (<100 words) and a detailed summary (<1000 words, scaled to content length)** for each article
6. Output summaries in **foldable `<details>` blocks** in Markdown

## Step 0: Output Language — Always Bilingual

This skill **always produces both Chinese and English outputs**. You will generate two separate Markdown files — one in Chinese, one in English. This means:
- Generate summaries in **both languages** for every article (Step 4)
- Assemble **two Markdown files** using the language-specific templates (Step 5)

**What changes by language:**

| Element | English file | Chinese file |
|---------|---------|---------|
| File header / intro | English | 中文 |
| Section headers (🚀 Headlines, etc.) | English labels | 中文标签 (e.g., 🚀 头条新闻) |
| Short summary | English | 中文 |
| Detailed summary | English | 中文 |
| Article titles & links | Original (unchanged) | Original (unchanged) |
| Category & read time labels | English | English (keep original) |
| Footer / generation note | English | 中文 |
 
---
 
## Extraction Workflow
 
### Step 1: Search Gmail for the Latest TLDR Newsletter
 
Use the `gws-gmail` skill to find the most recent TLDR newsletter email.
 
⚠️ **IMPORTANT: Match BOTH sender name AND email address.** All TLDR newsletters share the same email address `dan@tldrnewsletter.com`, but each category has a distinct sender display name (e.g., `TLDR AI`, `TLDR Dev`, `TLDR Fintech`). You MUST use `from:"<Sender Name>"` combined with `from:dan@tldrnewsletter.com` to correctly filter by category.
 
**For a specific category** (e.g., TLDR AI):
```
gmail_search_messages(q='from:"TLDR AI" from:dan@tldrnewsletter.com', maxResults=1)
```
 
**For any/all TLDR newsletters:**
```
gmail_search_messages(q="from:dan@tldrnewsletter.com", maxResults=5)
```
 
**Category-specific search queries (use sender display name for precise filtering):**
 
| Category | Sender Display Name | Search query |
|----------|-------------------|-------------|
| AI | `TLDR AI` | `from:"TLDR AI" from:dan@tldrnewsletter.com` |
| Tech (main) | `TLDR` | `from:"TLDR" from:dan@tldrnewsletter.com` (note: may also match other TLDR variants; verify the `From` header in results) |
| Dev | `TLDR Dev` | `from:"TLDR Dev" from:dan@tldrnewsletter.com` |
| Marketing | `TLDR Marketing` | `from:"TLDR Marketing" from:dan@tldrnewsletter.com` |
| Fintech | `TLDR Fintech` | `from:"TLDR Fintech" from:dan@tldrnewsletter.com` |
| InfoSec | `TLDR InfoSec` | `from:"TLDR InfoSec" from:dan@tldrnewsletter.com` |
| Product | `TLDR Product` | `from:"TLDR Product" from:dan@tldrnewsletter.com` |
| Design | `TLDR Design` | `from:"TLDR Design" from:dan@tldrnewsletter.com` |
 
**Verification step**: After getting search results, always check the `From` header in the returned message to confirm it matches the expected sender name (e.g., `TLDR AI <dan@tldrnewsletter.com>`). If results contain a different sender name, refine the query or pick the correct message.
 
If the user just says "TLDR" without specifying a category, search for the most recent emails from `dan@tldrnewsletter.com` and let them pick, or process the most recent one.
 
### Step 2: Read the Full Email Body
 
```
gmail_read_message(messageId="<message_id_from_step_1>")
```
 
The email body is plain text with a well-defined structure. Key parsing rules:
 
#### Email Body Structure
 
The TLDR newsletter email body follows this general pattern. The exact section headers and number of articles may vary, but the overall format is consistent:
 
```
TLDR AI 2026-03-10            ← Newsletter name and date
 
SPONSOR SECTION (skip)        ← Starts after "TOGETHER WITH [sponsor]"
                                 Ends before first section header
 
🚀
HEADLINES & LAUNCHES          ← START extraction here
 
 ARTICLE TITLE (X MINUTE READ) [N]
 
 TLDR's blurb paragraph...
 
 ANOTHER ARTICLE TITLE (X MINUTE READ) [N]
 
 TLDR's blurb...
 
🧠
DEEP DIVES & ANALYSIS
 
 ARTICLE TITLE (X MINUTE READ) [N]
 ...
 
🧑‍💻
ENGINEERING & RESEARCH
 
 DEBUG WITH AI... (SPONSOR) [N]  ← Skip any line with "(SPONSOR)"
 
 ARTICLE TITLE (X MINUTE READ) [N]
 ...
 
🎁
MISCELLANEOUS
 
 ARTICLE TITLE (X MINUTE READ) [N]
 ...
 
⚡
QUICK LINKS                   ← STOP extraction here

```
 
#### Parsing Rules
 
1. **Start extraction** at the first section header after the sponsor block. Section headers are marked by emoji icons followed by section names: `🚀 HEADLINES & LAUNCHES`, `🧠 DEEP DIVES & ANALYSIS`, `🧑‍💻 ENGINEERING & RESEARCH`, `🎁 MISCELLANEOUS`, etc.
 
2. **Stop extraction** at `⚡ QUICK LINKS`. Do NOT process Quick Links and content below it.
 
3. **Skip SPONSOR entries**: Any article title containing `(SPONSOR)` must be skipped entirely (both title and blurb).
 
4. **Extract for each article:**
   - **Title**: ALL CAPS text followed by `(X MINUTE READ)` — convert to Title Case in output
   - **Read time**: The `(X MINUTE READ)` part
   - **URL**: Found in the title line as a hyperlink (if available in the email body; if not, you may need to fetch the email's HTML content to extract links)
   - **TLDR blurb**: The paragraph(s) following the title, before the next title
   - **Category/section**: Determined by which section header the article falls under

### Step 3: Fetch Each Article's Original Content
 
⚠️ **MANDATORY — NO EXCEPTIONS: You MUST call `stealth-browser-mcp` on EVERY article URL.**
 
This is the most important step. **Do NOT skip any article.** Do NOT use TLDR's email blurb as a substitute for fetching the original. Do NOT cite "原文无法访问" unless you have actually attempted the fetch and it genuinely failed.
 
**Compliance checklist (enforce strictly):**
1. For EVERY article extracted in Step 2, call `stealth-browser-mcp` with the article's URL
2. If you find yourself writing "原文无法访问" for more than 3 articles in a single run, stop and re-examine — you are likely skipping fetches
3. Never batch-skip articles to "save tool calls" — thoroughness is more important than speed
 
 
**Fetch rules:**
- Use `stealth-browser-mcp` for better handling of dynamic content and paywalls.
- **CRITICAL: Call browser tools SEQUENTIALLY (one at a time).** Do NOT make parallel browser MCP calls — the browser instance is shared and concurrent calls will cause race conditions, navigation conflicts, and data corruption. Process each article URL serially before moving to the next.
- If a fetch genuinely fails (timeout, 403, paywall), try `web_search` with the article title to find alternative coverage or cached content. If web search also fails, fall back to TLDR's own blurb for the short summary and note the failure in the detailed summary. Include the error notice in both language files — Chinese: "⚠️ 原文无法访问（已尝试抓取及搜索，返回错误：[具体错误]）", English: "⚠️ Original article unavailable (fetch and search attempted, error: [specific error])"
- If all above methods fail, ask the user to provide the article content directly (e.g., "I wasn't able to access the original article for [Article Title][URL]. If you have access, please provide the content or key points you'd like summarized.")
 
### Step 4: Generate Summaries (Bilingual)
 
For each article, generate summaries in **both Chinese and English** from the fetched content. Each article gets four summaries total:

#### Short Summary (短摘要) — one Chinese, one English
- **Max 100 words** (per language)
- One paragraph, no bullet points
- Capture the single most important takeaway
 
#### Detailed Summary (详细摘要) — one Chinese, one English
- **Scaled to original content length, max 1000 words** (per language)
- Scaling guide:
  - 1-2 min read (~500 words original) → ~150-200 word summary
  - 3-5 min read (~1000-1500 words original) → ~300-500 word summary
  - 5-10 min read (~2000-3000 words original) → ~600-800 word summary
  - 10+ min read (3000+ words original) → up to 1000 word summary
- Structured paragraphs covering: main thesis, key evidence/data, implications, and context
- May include brief bullet points for listing multiple findings or features
- Maintain factual accuracy — do not hallucinate details not in the source
 
### Step 5: Assemble Two Markdown Files with Foldable Blocks

Produce **two files** — one Chinese, one English — using the same structure but different language content.

#### Section Header Mapping

| Email Section | Chinese file header | English file header |
|---------------|------------------------|------------------------|
| HEADLINES & LAUNCHES | 🚀 头条新闻 | 🚀 Headlines & Launches |
| DEEP DIVES & ANALYSIS | 🧠 深度分析 | 🧠 Deep Dives & Analysis |
| ENGINEERING & RESEARCH | 🧑‍💻 工程与研究 | 🧑‍💻 Engineering & Research |
| MISCELLANEOUS | 🎁 杂项 | 🎁 Miscellaneous |

#### Chinese file template

```markdown
# TLDR AI News - 2026-03-10 (link using the "View Online" URL from the email)

> 自动从 TLDR AI Newsletter 提取的科技新闻摘要（含 AI 生成的短摘要与详细摘要）

---

## 🚀 头条新闻

### [Article Title](https://link-to-article)
**X minute read**

📋 Chinese short summary here...

<details>
<summary>📖 详细摘要</summary>

Chinese detailed summary here...

</details>

```

#### English file template

```markdown
# TLDR AI News - 2026-03-10 (link using the "View Online" URL from the email)

> Auto-extracted tech news summaries from TLDR AI Newsletter (with AI-generated short & detailed summaries)

---

## 🚀 Headlines & Launches

### [Article Title](https://link-to-article)
**X minute read**

📋 English short summary here...

<details>
<summary>📖 Detailed Summary</summary>

English detailed summary here...

</details>

```

**Formatting notes:**
- Always include a blank line after `<summary>` closing tag and before content
- Always include a blank line before `</details>` closing tag

## Error Handling
 
- If Gmail search returns no results, inform the user and suggest checking their subscriptions
- If `gmail_read_message` returns an empty body, tell the user and ask for next steps (e.g., try a different category, or provide the email content directly)
- **NEVER** write a fetch-failure notice without having actually called `stealth-browser-mcp`
- If the email body structure doesn't match expected format, fall back to best-effort parsing and note any issues
 
