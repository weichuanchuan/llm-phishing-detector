# MailCheck: Email Security Analysis System

Try it yourself: [mailcheck.help](https://mailcheck.help)
View example report: [Report](https://mailcheck.help/result?r=6875a1b4-0d27-4a8c-8773-c1a1efb1c88c)

## Overview

MailCheck is a comprehensive phishing detection system developed as part of a bachelor's thesis. The system combines heuristic technical analyses with linguistic evaluation using Large Language Models (LLMs) to provide transparent, educational feedback about potential phishing threats in emails.

Unlike traditional "black box" detection systems, MailCheck focuses on providing structured, user-friendly explanations that help users understand why an email might be suspicious, thereby enhancing their cybersecurity awareness and decision-making abilities.

## Features

- **Email Header Analysis**: Examines email headers for signs of spoofing, checks sender domains against blacklists, and verifies DKIM and SPF records.
- **URL Security Checks**: Crawls and analyzes all URLs found in emails, follows redirects, and checks against known blacklists.
- **Attachment Scanning**: Scans email attachments for malware using ClamAV.
- **LLM-Based Content Analysis**: Uses AI to analyze the linguistic patterns, tone, and structure of emails for signs of phishing.
- **Educational Feedback**: Provides detailed explanations of security issues rather than simple "safe/unsafe" classifications.
- **Multi-Platform Access**: Accessible via both email submission and web interface.
- **Screenshot Capture**: Takes screenshots of linked websites for visual verification.
- **Whitelist Support**: Maintains a whitelist of trusted domains to reduce false positives.
- **Rate Limiting**: Implements rate limiting to prevent abuse of the service.

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

## Installation

### Prerequisites
- Node.js 18+ and npm
- ClamAV installed on the host (used for attachment scanning)
- Chromium/Chrome available on the host (Puppeteer will use its bundled browser if available or the executable path you provide)
- A mail server for sending/receiving emails
- An OpenRouter API key for LLM access

### Local Installation (no Docker)

You can run the project directly on Windows, macOS, or Linux without containers. The Windows steps below are PowerShell-friendly; bash users can follow the same sequence with the listed commands.

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd mailcheck
   ```

2. Create your environment file from the template and fill in credentials:
   ```bash
   # PowerShell
   copy .env.example .env

   # Git Bash / WSL
   cp .env.example .env
   ```

   Required variables:
   - `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`: SMTP details for sending reports.
   - `MAIL_SERVER_FS`: Path to your Maildir for ingesting EML files (defaults to `./data/mailserver`).
   - `GOOGLE_SAFE_BROWSING_API_KEY` and `OPENROUTER_API_KEY`: API keys for URL checks and LLM analysis.
   - `PUPPETEER_EXECUTABLE_PATH` (optional): Point to a local Chrome/Chromium binary if Puppeteer's bundled browser should be overridden.

3. Install dependencies and prepare local data folders:
   ```bash
   npm install
   npm run setup:local
   ```

4. Start the application directly with Node.js (both `npm start` and `npm run start` work):
   ```bash
   npm start
   ```

   The terminal will print clickable links such as `http://localhost:3000` and `http://localhost:3000/index.html` so you can jump straight to the frontend. The server listens on `http://localhost:3000` (or the `PORT` you set). Screenshots, feedback, and reports are written under `data/tmp/` in the project root.

5. Stop the application with `Ctrl+C` in the terminal.

#### Windows-specific notes

- **Node.js and npm**: Install the latest LTS release from [nodejs.org](https://nodejs.org/). Confirm installation with `node -v` and `npm -v` in PowerShell.
- **ClamAV**: Install the official Windows build (or use [ClamWin](https://www.clamwin.com/)) and ensure the `clamscan.exe` path is in your `PATH` so the `clamscan` npm package can invoke it.
- **Chromium/Chrome**: If the bundled Puppeteer binary cannot launch on your machine, install Chrome/Edge and set `PUPPETEER_EXECUTABLE_PATH` in `.env` to the browser executable (for example, `C:\Program Files\Google\Chrome\Application\chrome.exe`).
- **Maildir path**: The default `MAIL_SERVER_FS=./data/mailserver` works on Windows. If you point it elsewhere, use Windows paths (e.g., `C:\mailcheck\maildir`).
- **Shell choice**: All npm scripts run in PowerShell, Git Bash, or WSL. When using PowerShell, prefer the `copy` command shown above to create `.env`.

### Docker Compose Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd mailcheck
   ```

2. Create a `.env` file (see `.env.example` for required variables).

3. Start the application with Docker Compose:
   ```bash
   docker compose up -d
   ```

   This will:
   - Build the Docker image with Node.js, ClamAV, and Chromium
   - Mount the data directory for persistence
   - Configure the mail server directory
   - Start the application on port 3000

4. View logs:
   ```bash
   docker compose logs -f
   ```

5. Stop the application:
   ```bash
   docker compose down
   ```

### One-Click Docker Deployment

For a streamlined setup that builds the image, creates required directories, and ensures the Traefik network exists, run:

```bash
./run.sh
```

Prerequisites:
- Docker with Docker Compose v2 available via `docker compose`
- A populated `.env` file (including `MAIL_SERVER_FS`)
- Permissions to create the `traefik_web` Docker network if it does not already exist

## Usage

### Live Demo
A live demo of the system is hosted at [mailcheck.help](https://mailcheck.help). You can use this demo to test the system without installing it locally.

### Email Submission
Send an email to the configured email address. The system will analyze the email and respond with a detailed security report.

### Web Interface
1. Access the web interface at `http://localhost:3000` (or [mailcheck.help](https://mailcheck.help) for the live demo)
2. Upload an EML file for analysis
3. View the detailed security report

### API Endpoints
- `POST /analyze`: Submit an EML file for analysis
- `GET /explain/:term`: Get explanation for security terms
- `GET /screenshot/:uuid`: View screenshots of websites
- `POST /feedback`: Submit feedback about the analysis
- `POST /persist`: Save analysis results
- `GET /persist/:uuid`: Retrieve saved analysis results

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
├── data/                  # Data files and public assets
│   ├── mailserver/        # Email storage for filesystem-based mail server
│   ├── prompts/           # LLM prompt templates
│   └── public/            # Public web assets
├── src/                   # Source code
│   ├── config/            # Configuration files
│   ├── http/              # Web interface controllers and routes
│   ├── mails/             # Email processing components
│   ├── tests/             # Security test suites
│   ├── url/               # URL analysis components
│   └── utils/             # Utility functions
├── Dockerfile             # Docker configuration
└── compose.yml            # Docker Compose configuration
```

### Data Directory Structure

The `data` directory contains several important components:

#### Mailserver Directory
The `mailserver` directory is used for the filesystem-based mail server implementation. It follows the Maildir format with subdirectories:
- `cur`: Contains current messages that have been seen
- `new`: Contains new messages that have not been seen yet
- `home`: Contains processed messages

The mailserver directory is configured in the `.env` file via the `MAIL_SERVER_FS` variable and is monitored by the system for new incoming emails.

#### Prompts Directory
The `prompts` directory contains template files used by the LLM for analysis:
- `prompt_eml.txt`: Prompt template for analyzing complete EML files
- `prompt_no_eml.txt`: Prompt template for analyzing forwarded emails without full headers

#### Public Directory
The `public` directory contains web assets and configuration files:
- `index.html`: Main landing page
- `result.html`: Template for displaying analysis results
- `how.html`: Instructions on how to use the system
- `study.html`: Information about the research study
- `feedback.js`: JavaScript for handling user feedback
- `whitelist.txt`: List of trusted domains that bypass certain security checks
During runtime, the system also creates a `tmp` directory within `data` for storing:
- Screenshots of analyzed websites
- Log files
- Temporary analysis reports
- User feedback data

### Building
```bash
npm run build
```

## Research Background

This project was developed as part of a bachelor's thesis addressing the challenge of phishing emails, which continue to pose a significant cybersecurity risk by exploiting human vulnerabilities. Traditional detection systems often operate as black boxes, offering little transparency or educational value to users.

The system combines heuristic technical analyses (header verification, link inspection) with linguistic evaluation using LLMs. The LLM not only analyzes the general tone and structure of the email but also formulates individualized explanations and trust assessments, taking into account both language patterns and results from technical checks.

A small-scale user study was conducted to gather qualitative feedback regarding the clarity, usability, and educational impact of the generated reports. Results indicate that structured, transparent feedback can enhance user understanding of phishing risks, although further improvements are needed, particularly in simplifying technical terms and explaining scoring mechanisms.
