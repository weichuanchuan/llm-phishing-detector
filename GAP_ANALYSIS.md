# Python port coverage vs original MailCheck

This document summarizes which bachelor-thesis features from the TypeScript reference remain unported in the current Python FastAPI implementation and highlights where the Python stack diverges.

## What the Python port does today
- Heuristic-only analysis: scoring is derived from header anomalies, URL patterns, attachment MIME checks, and keyword hits; there is no LLM or external blacklist callout in this pipeline.
- URL crawling collects redirect and status data but skips screenshot capture.
- Drop-folder processing persists results as JSON without emailing reports.

Relevant implementation hotspots:
- `app/analyzer.py` runs SPF lookups, reply-to mismatches, keyword checks, and lightweight URL heuristics before computing a score.【F:app/analyzer.py†L37-L242】
- The FastAPI service exposes `/analyze`, `/persist`, `/feedback`, and UI/static assets but does not integrate screenshot serving or mail sending endpoints.【F:app/main.py†L26-L106】

## Features missing versus TypeScript reference
- **LLM-backed content analysis** — the thesis version prompts an LLM for threats and trust scoring, which is absent from the Python analyzer.【F:src/tests/llm_test_suite.ts†L1-L76】【F:src/tests/llm_test_suite.ts†L83-L118】
- **Blacklist & DNS safety checks** — Google Safe Browsing and DBL lookups are implemented in the TypeScript domain checker but have no Python equivalent.【F:src/url/domain_checker.ts†L1-L134】
- **Automated website screenshots** — Puppeteer-based crawling captures page screenshots and stores UUID-addressable artifacts in the reference stack; the Python URL scanner omits this flow.【F:src/url/url_crawler.ts†L133-L230】【F:src/http/controllers/screenshot.controller.ts†L1-L34】
- **Email report rendering & delivery** — the original mails the analysis (including screenshot preview links) using HTML templates; the Python port only writes reports to disk.【F:src/mails/mail_sender.ts†L587-L625】
- **Attachment malware scanning** — ClamAV-backed checks in the TypeScript flow are not present in the Python codebase (only MIME-type heuristics are applied).【F:app/analyzer.py†L90-L103】
- **DKIM/DMARC verification** — beyond SPF TXT lookups, the Python analyzer does not verify DKIM signatures or enforce DMARC alignment that exist in the thesis tooling.【F:app/analyzer.py†L150-L217】

## Next steps
Addressing the gaps above would bring the Python reproduction closer to the thesis behavior: wiring LLM prompts into the analyzer, porting Safe Browsing/DBL checks, adding screenshot capture and serving, integrating ClamAV plus DKIM/DMARC validation, and restoring email-based report delivery.
