# Wiki Schema — HCendGame FWA Detection

This file is the schema layer. It governs how the wiki is structured, maintained, and extended.

---

## Directory Layout

```
wiki/
  schema.md          ← this file (LLM reads first on every session)
  index.md           ← content catalog, all pages with one-line summaries
  log.md             ← append-only chronological activity log
  sources/           ← immutable raw sources (papers, specs, docs)
  pages/
    concepts/        ← domain concepts (FWA, HCC, ICD-10, FHIR, MCP...)
    decisions/       ← architectural and implementation decisions
    entities/        ← named entities (tools, APIs, platforms, providers)
    lessons/         ← lessons learned, gotchas, fixes
```

---

## Page Conventions

- Each page is a single `.md` file, named in `kebab-case`
- First line: `# Title`
- Second block: `**Tags**: tag1, tag2, tag3`
- Body: free-form markdown
- End: `**Related**: [[other-page]], [[another-page]]`
- Double-brackets `[[page-name]]` = cross-reference (Obsidian-compatible)

---

## Operations

### Ingest
When a new source (article, doc, conversation finding) arrives:
1. Read relevant existing wiki pages
2. Extract key facts, update or create pages
3. Update `index.md` if a new page was created
4. Append to `log.md`: `[date] ingest: <source> → <pages affected>`
5. Flag contradictions with `> ⚠️ CONTRADICTION: ...` blockquote

### Query
When user asks a question:
1. Search relevant wiki pages (via index.md)
2. Synthesize answer with `[[page]]` citations
3. If the answer reveals a gap, create a new stub page
4. Append to `log.md`: `[date] query: <question> → <pages used>`

### Lint (periodic)
Check for:
- Orphaned pages not in index.md
- Broken `[[cross-references]]`
- Stale claims (check against current code/deploy)
- Missing related-links

---

## Scope

This wiki covers:
- Healthcare FWA domain knowledge (ICD-10, NDC, HCC, CMS)
- MCP protocol implementation (SHARP extension, Prompt Opinion)
- FHIR R4 integration patterns
- AutoResearch / Karpathy LOOP FOREVER pattern
- Architecture decisions for rxhcc-app
- Lessons from hackathon sprint development
