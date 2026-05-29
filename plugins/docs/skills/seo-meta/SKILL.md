---
name: seo-meta
description: >
  Generates SEO metadata (slug, subtitle, tags, title, description) for markdown articles as YAML
  frontmatter. Use when the user asks to add metadata, SEO info, tags, or frontmatter to an article,
  or wants to prepare a markdown post for publishing.
---

# SEO Meta Generator

Generate structured SEO metadata for a markdown article and insert it as YAML frontmatter.

## Step 1: Get the file

Ask the user for the markdown file path if they haven't provided one. Read the full content using the Read tool.

## Step 2: Detect language

Determine the primary language of the article from its content. If the user has explicitly specified a language in the conversation, use that instead. All generated metadata fields must be written in the detected (or specified) language.

## Step 3: Check for existing frontmatter

If the file already starts with a `---` YAML frontmatter block, parse it. Only generate metadata fields that are **missing** from the existing frontmatter. Preserve all existing fields and their values — never overwrite them.

The five metadata fields this skill manages are: `slug`, `subtitle`, `tags`, `seo_title`, `seo_description`.

## Step 4: Generate metadata

For each missing field, generate it according to these guidelines:

### slug
- Kebab-case, maximum 60 characters
- Derived from the article's core topic, not a mechanical transliteration of the title
- Omit stop words (the, a, an, of, in, etc.) and trailing hyphens
- For non-Latin languages, use a romanized/transliterated version of the key concept
- Example: `nextjs-app-router-data-fetching`

### subtitle
- 1-2 sentences that summarize the article's value proposition
- Should complement the title, not repeat it — tell the reader what they'll gain
- Example: `Learn how to fetch data efficiently in Next.js App Router using Server Components, with practical patterns for real-world applications.`

### tags
- Exactly 5 tags
- Lowercase, no special characters
- Always in English, regardless of the article's language — tags serve as universal categorization keys
- A mix of broad category tags (e.g., `web development`) and specific topic tags (e.g., `nextjs`, `server-components`)
- Tags should help readers discover the article through browsing and search

### seo_title
- 50-60 characters long
- Includes the primary keyword naturally
- Compelling and click-worthy for search results — not just the article title repeated
- Example: `Next.js Data Fetching: App Router Patterns That Scale`

### seo_description
- 120-160 characters long
- Includes the primary keyword
- Action-oriented or curiosity-driven — gives the searcher a reason to click
- Example: `Master Next.js App Router data fetching with Server Components. Practical patterns for static, dynamic, and streaming data in production apps.`

## Step 5: Present to user for confirmation

Show the generated metadata in YAML format and ask the user to confirm before writing. Use AskUserQuestion with a preview showing the exact frontmatter that will be inserted. Give the user the option to approve, edit specific fields, or regenerate.

Use this template when presenting:

```yaml
---
slug: example-article-slug
subtitle: >-
  A concise summary of what this article covers and why it matters.
tags:
  - tag1
  - tag2
  - tag3
  - tag4
  - tag5
seo_title: Compelling SEO Title With Primary Keyword
seo_description: >-
  A 120-160 character meta description that includes the primary keyword and encourages clicks.
---
```

## Step 6: Write to file

After user confirmation:

- **No existing frontmatter**: Prepend the full `---` block at the top of the file using the Edit tool.
- **Existing frontmatter**: Merge the new fields into the existing frontmatter block using the Edit tool. Insert the new fields before the closing `---`, keeping the original fields in their original order.

## Hard rules

- Never modify the article body content — only touch the frontmatter section
- Always confirm with the user before writing to the file
- Tags must be exactly 5
- Slug must be kebab-case, max 60 characters
- SEO title should be 50-60 characters
- SEO description should be 120-160 characters
- All metadata must be in the same language as the article, unless the user explicitly requests a different language
- For non-Latin scripts (Chinese, Japanese, Korean, Arabic, etc.), the slug should use romanized/transliterated keywords
