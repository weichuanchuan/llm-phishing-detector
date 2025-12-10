# Project review and open issues

This repository mixes the original TypeScript thesis source and the newer FastAPI-based Python port. Several gaps and blockers remain:

## Environment and dependency readiness
- `pip install -r requirements.txt` currently fails in this sandbox because the proxy returns HTTP 403 while resolving `aiohttp`, preventing local installs and container builds until network access is restored. See the captured installer output for details.

## Documentation mismatches
- The README still describes TypeScript-specific components (e.g., `mail_server_fs_mount.ts`, `domain_checker.ts`, `header_test_suite.ts`) even though the FastAPI app runs from `app/`. Readers may believe those modules are active when only the Python service is wired up.

## Functional gaps vs. thesis reference
- The FastAPI analyzer implements SPF header checks, URL heuristics, attachment MIME sniffing, and keyword flags, but it omits LLM-backed content analysis, ClamAV malware scanning, DKIM/DMARC verification, screenshot capture/serving, and email-based report delivery that exist in the TypeScript stack. These differences are summarized in `GAP_ANALYSIS.md` and are visible in the Python analyzer implementation.
