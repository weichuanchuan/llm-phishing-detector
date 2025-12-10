# MailCheck: Email Security Analysis System

![MailCheck Demo](https://raw.githubusercontent.com/jannikhst/llm-phishing-detector/main/data/public/gif/screenshot-2025-08-08-000275.gif)

Try it yourself: [mailcheck.help](https://mailcheck.help)
View example report: [Report](https://mailcheck.help/result?r=6875a1b4-0d27-4a8c-8773-c1a1efb1c88c)

## Overview

MailCheck is a comprehensive phishing detection system developed as part of a bachelor's thesis. The system combines heuristic technical analyses with linguistic evaluation using Large Language Models (LLMs) to provide transparent, educational feedback about potential phishing threats in emails.

Unlike traditional "black box" detection systems, MailCheck focuses on providing structured, user-friendly explanations that help users understand why an email might be suspicious, thereby enhancing their cybersecurity awareness and decision-making abilities.

## Features (TypeScript reference implementation)

- **Email Header Analysis**: Examines email headers for signs of spoofing, checks sender domains against blacklists, and verifies DKIM and SPF records.
- **URL Security Checks**: Crawls and analyzes all URLs found in emails, follows redirects, and checks against known blacklists.
- **Attachment Scanning**: Scans email attachments for malware using ClamAV.
- **LLM-Based Content Analysis**: Uses AI to analyze the linguistic patterns, tone, and structure of emails for signs of phishing.
- **Educational Feedback**: Provides detailed explanations of security issues rather than simple "safe/unsafe" classifications.
- **Multi-Platform Access**: Accessible via both email submission and web interface.
- **Screenshot Capture**: Takes screenshots of linked websites for visual verification.
- **Whitelist Support**: Maintains a whitelist of trusted domains to reduce false positives.
- **Rate Limiting**: Implements rate limiting to prevent abuse of the service.

## Python reproduction coverage

The FastAPI-based Python port focuses on heuristic analysis, a drop-folder watcher, and the browser UI. Some thesis-era capabilities have **not** been re-implemented yet:

- LLM-backed content analysis is not wired up; only keyword and header/link heuristics run today.
- ClamAV-powered attachment scanning, DKIM/DMARC verification, and blacklist lookups are absent from the Python analyzer.
- Automated website screenshots, email report delivery, and the screenshot-serving routes remain available only in the TypeScript implementation.

Refer to `GAP_ANALYSIS.md` for a detailed side-by-side feature comparison between the original TypeScript stack and the current Python port.

## System Architecture

The system is organized into several key components:

### Mail Processing
- `mail_server_fs_mount.ts`: Monitors filesystem for new email files
- `eml_parser.ts`: Parses email content and structure
- `mail_sender.ts`: Generates and sends security reports
- `verify.ts`: Verifies email authenticity (DKIM, SPF)
- `rate_limit.ts`: Implements rate limiting for email submissions

### URL Analysis
- `domain_checker.ts`: Checks domains against blacklists
- `url_checker.ts`: Coordinates URL security checks
- `url_crawler.ts`: Crawls websites to analyze content and follow redirects
- `whitelist.ts`: Manages whitelist of trusted domains

### Security Testing
- `header_test_suite.ts`: Tests for header-based security issues
- `link_test_suite.ts`: Tests for URL-based security issues
- `llm_test_suite.ts`: Uses AI to analyze email content
- `test_suite_runner.ts`: Coordinates all security tests

### Web Interface
- HTTP controllers and routes for web-based submissions
- Screenshot management for visual verification of websites

## Installation (Python reproduction)

The repository now contains a full Python/FastAPI reproduction that mirrors the original MailCheck flow: file-system mailbox monitoring, SPF-aware header checks, URL crawling, persistence, and feedback logging. The Python services reuse the public data and prompt assets from the thesis version.

### Prerequisites
- Docker with the Compose plugin
- (Optional) Sample `.eml` files to drop into `data/mailserver/start` or upload through the API

### One-command startup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd mailcheck
   ```

2. Start the stack (build + run) with the helper script:
   ```bash
   ./run.sh
   ```

   The script prepares persistence directories (`data/tmp/reports`), the watched mail drop (`data/mailserver/start`), builds the Python image, and serves the API on port `3000`.

3. Open the browser UI at [http://localhost:3000](http://localhost:3000) to upload `.eml` files, fetch saved reports by UUID, and send quick feedback. Interactive API docs remain available at [http://localhost:3000/docs](http://localhost:3000/docs).

Stop the stack anytime with `Ctrl+C` or by running `docker compose down` in the project root.

## Usage

### Live Demo
A live demo of the system is hosted at [mailcheck.help](https://mailcheck.help). You can use this demo to test the system without installing it locally.

### Email Submission
Send an email to the configured email address. The system will analyze the email and respond with a detailed security report.

### Web Interface
1. Access the web interface at `http://localhost:3000` (or [mailcheck.help](https://mailcheck.help) for the live demo)
2. Upload an EML file for analysis (optionally persisting the report)
3. View the detailed security report, copy the UUID, and provide optional 1–5 feedback

### Drop-folder processing
- Copy `.eml` files into `data/mailserver/start` while the Python container is running.
- The watchdog listener automatically parses each file, runs the same analysis pipeline, and stores the report JSON into `data/tmp/reports`.

### API Endpoints (FastAPI)
- `GET /health`: Simple health probe used by Docker Compose
- `POST /analyze`: Upload an `.eml` file and get a heuristic phishing analysis (optionally `persist=true`)
- `GET /explain/{term}`: Request definitions of security terms (SPF, DKIM, DMARC, link hygiene)
- `POST /feedback`: Store user feedback tied to a report UUID
- `POST /persist`: Save an analysis result explicitly
- `GET /persist/{uuid}`: Retrieve a persisted report by UUID

## Configuration

### Whitelist Configuration
Edit `data/public/whitelist.txt` to add trusted domains that should bypass certain security checks.

### LLM Configuration
The system uses OpenRouter to access various AI models. Configure the model in `src/tests/llm_test_suite.ts`.

### ClamAV Configuration
ClamAV is used for malware scanning. Ensure it's properly installed and configured on your system.

## Development

### Project Structure
```
├── app/                     # Python FastAPI source code
│   ├── analyzer.py          # Heuristic phishing checks plus SPF lookup and URL crawling
│   ├── config.py            # Shared paths and analysis constants
│   ├── eml_utils.py         # EML parsing helpers, nested attachment handling, drop-folder utilities
│   ├── main.py              # API entrypoint and file-system mail watcher bootstrap
│   ├── models.py            # Pydantic schemas for requests/responses
│   ├── rate_limit.py        # Sliding-window sender limiter
│   ├── storage.py           # Lightweight JSON persistence + feedback log
│   ├── url_scanner.py       # Async HTTP crawler used during analysis
│   ├── watcher.py           # Watchdog-powered monitor for `data/mailserver/start`
│   └── static/              # Browser UI (index.html, styles, and JS)
├── data/                    # Public assets and example configuration
│   ├── public/              # Whitelist and static files reused from the thesis
│   └── tmp/                 # Created automatically for persisted reports/feedback
├── Dockerfile               # Python 3.11 container definition
├── compose.yml              # Docker Compose service for the API
└── run.sh                   # Helper script to build and start the stack
```

### Data Directory Structure

The `data` directory still carries public assets from the thesis version and now also stores runtime artifacts:

- `public/whitelist.txt`: Trusted domains skipped during URL red-flag checks.
- `tmp/`: Created on startup to hold persisted analysis JSON files and feedback logs.

You can drop sample `.eml` files anywhere locally; they are uploaded to the API at request time and are not stored automatically unless `persist=true` is used.

## Research Background

This project was developed as part of a bachelor's thesis addressing the challenge of phishing emails, which continue to pose a significant cybersecurity risk by exploiting human vulnerabilities. Traditional detection systems often operate as black boxes, offering little transparency or educational value to users.

The system combines heuristic technical analyses (header verification, link inspection) with linguistic evaluation using LLMs. The LLM not only analyzes the general tone and structure of the email but also formulates individualized explanations and trust assessments, taking into account both language patterns and results from technical checks.

A small-scale user study was conducted to gather qualitative feedback regarding the clarity, usability, and educational impact of the generated reports. Results indicate that structured, transparent feedback can enhance user understanding of phishing risks, although further improvements are needed, particularly in simplifying technical terms and explaining scoring mechanisms.
