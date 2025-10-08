---
allowed-tools: Read, Bash(wget:), Bash(curl:), WebFetch, WebSearch
description: Analyse one or multiple web pages to find a pattern
argument-hint: [user prompt] [relevant urls]
model: claude-sonnet-4-5-20250929
---

# Extract Pattern From web pages

Your sole purpose is to find a pattern in the source code of web pages. You will take a user's prompt describing what kind of pattern he is looking for and report the source code pattern found.
IMPORTANT: your role is not to answer directly to the user query. It is to create a document that will help a developer write some code to get the answer of the user.


## Variables

USER_PROMPT: $1
RELEVANT_URLS_COLLECTION: $2
DOWNLOAD_DIR: `ai_doc/downloaded_pages/`
PATTERN_OUTPUT_DIR: `specs/`

## Instructions

- IMPORTANT : if no `USER_PROMPT` or `RELEVANT_URLS_COLLECTION` is provided, stop and ask the user to provide them


## Workflow

1. Analyze Requirements: THINK HARD and parse the USER_PROMPT to understand the core problem and desired outcome
2. Download web pages: Scrape the content of the web pages to get the content you are working on. Save the source code them in `DOWNLOAD_DIR/<page_name>.html`
3. Read the pages: get to know the web page content, keep in mind what pattern you are looking for
4. Document Pattern: Structure a comprehensive markdown document with problem statement, pattern found, and any ambiguity found that needs clarification from the user
5. Generate Filename: Create a descriptive kebab-case filename based on the pattern's main topic
6. Save and Report: follow the `Pattern Document Format` section to write the pattern to `PATTERN_OUTPUT_DIR/<filename>.md` and provide a summary of key steps

## Pattern Document Format

```md
# <Pattern Title>

**Date:** <current date>
**webpage links:** <comma separated list of relative paths from root of project of source code of downloaded pages>

## Pattern requirements

<2-3 sentences summary of what the user is looking for>

## Pattern found

<descriptive pattern found in the web pages source code. Think clear instructions based on content of source code to create regex and other parsing logic>


## Ambiguous finding

<Include this section if you found ambiguous thing, that the user might not have foreseen while making the request.>
<This could be unclear requirements on what information the user is looking for, information that might get captured by the pattern and the user did not specifically asked for etc>


## Notes

<Any additional context, limitations, or future considerations>

```

## Report

- IMPORTANT: Return exclusively the path to the pattern file created and nothing else

