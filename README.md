# Nazer 🛡️

A lightweight, CLI-based HTTP Proxy Logger & Active Spider.

**Developed by [@RaqinAlAsraar](https://github.com/RaqinAlAsraar)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-lightgrey.svg)](#installation)

---

## Table of Contents

- [The Motive](#the-motive)
- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
  - [Debian / Ubuntu / Kali Linux (Recommended)](#for-debian--ubuntu--kali-linux-recommended)
  - [Manual Installation (Windows / macOS / Arch)](#manual-installation-windows--macos--arch)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Fast Execution](#fast-execution-targeted)
  - [Configuration](#configuration)
- [Fixing SSL Certificate Errors](#fixing-ssl-certificate-errors-manual-proxy-setup)
- [Output Formats](#output-formats)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## The Motive

I built this tool for my daily target mapping workflow during bug bounty hunting because I needed a quick, lightweight way to log API endpoints and urls call by target in backend. Nazer runs quietly in the terminal while you surf a target website. It focuses purely on mapping the target and gives outputs exactly as per our needs, dropping everything into a clean, searchable HTML or CSV file. Paired with the built-in active spider, it serves as a lightning-fast recon tool that perfectly fits everyday testing needs.

## Features

| Feature | Description |
|---|---|
| 🗂️ **Multi-Format Logging** | Dumps history into dynamic HTML, CSV, or zero-memory JSONL. |
| ♻️ **Auto-Deduplication** | Only logs unique `Method + URL` combinations. Say goodbye to proxy noise. |
| 🕷️ **Active Spider** | Silently parses HTML/JS for hidden links and fetches them in the background. |
| 🎯 **Initiator Tracking** | Tells you if a request was clicked by a User, loaded by the Website, or fetched by the Spider. |
| 📋 **Header Capture** | Optionally logs full HTTP request/response headers in the HTML UI. |
| 🌐 **Sandboxed Browser** | Automatically launches Chromium/Chrome pre-configured to bypass cert errors. |

## Screenshots

`![Nazer CLI](images/1.png)`

`![Nazer HTML UI](images/2.png)`

---

## Installation

### For Debian / Ubuntu / Kali Linux (Recommended)

An installer script is included that sets up a secure Python virtual environment and links the command globally.

```bash
git clone https://github.com/RaqinAlAsraar/nazer.git
cd nazer
chmod +x install.sh
./install.sh
```

### Manual Installation (Windows / macOS / Arch)

```bash
git clone https://github.com/RaqinAlAsraar/nazer.git
cd nazer
pip install -r requirements.txt
python nazer.py
```

---

## Usage

If you installed via the bash script, you can run Nazer from any directory. Logs are automatically saved in the folder where you execute the command.

### Interactive Mode

```bash
nazer
```

Launches a guided prompt where you set the target, output formats, and spider behavior on the fly.

### Fast Execution (Targeted)

```bash
nazer -d target.com -f html,csv
```

| Flag | Description |
|---|---|
| `-d`, `--domain` | Target domain to scope the proxy/spider to. |
| `-f`, `--formats` | Comma-separated output formats: `html`, `csv`, `jsonl`. |

Run `nazer -h` for the full list of available flags.

### Configuration

On its first run, Nazer creates a global configuration file at `~/.nazer/config.json`. Edit this file to change the default port (`8080`), toggle the background spider, or enable header logging.

---

## Fixing SSL Certificate Errors (Manual Proxy Setup)

By default, Nazer tries to launch a sandboxed Chromium instance that automatically ignores SSL errors. However, if you disable `auto_launch_browser` in your config and connect your own browser (like Firefox) to `127.0.0.1:8080`, every HTTPS site will throw a security warning.

To fix this permanently:

1. Start Nazer in your terminal.
2. Configure your browser to use `127.0.0.1:8080` as its HTTP/HTTPS proxy.
3. Open that browser and go exactly to `http://mitm.it` (make sure it's `http://`, not `https://`).
4. Download the certificate for your operating system.
5. Import that certificate into your browser's trusted Root Certificate Authorities.

---

## Output Formats

| Format | Best for |
|---|---|
| **HTML** | Interactive, searchable DataTables UI — great for manual review and headers. |
| **CSV** | Quick imports into spreadsheets or other recon tooling. |
| **JSONL** | Zero-memory streaming log, ideal for piping into scripts (`jq`, Python, etc.) for automated triage. |

---

## Disclaimer

Nazer is a reconnaissance and traffic-logging tool intended for authorized security testing, bug bounty work, and personal research. Only use it against targets you own or have **explicit written permission** to test. The author is not responsible for misuse or damage caused by this tool.

## License

Distributed under the MIT License. See `LICENSE` for more information.
