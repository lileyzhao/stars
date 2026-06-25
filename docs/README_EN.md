# 🌟 Stars

<img src="https://img.shields.io/badge/status-Development-brightgreen" alt="Status: Development"> <img src="https://img.shields.io/badge/version-0.1.1-blue" alt="Version"> <img src="https://img.shields.io/badge/license-MIT-orange" alt="License">

> **Intelligently organize your GitHub stars and discover hidden knowledge galaxies**

[English](README_EN.md) | [简体中文](README.md)

## 🚀 Project Overview

**Stars** is a powerful GitHub star organization tool that leverages AI to transform your scattered GitHub star collection into a well-organized knowledge universe. No more manual sorting of hundreds of projects accumulated over time - let artificial intelligence map your knowledge galaxy.

```
"In the vast sea of stars, each star has its own story and belonging."
```

## ✨ Core Features

- **🔍 GitHub Integration**: Automatically fetch all your starred projects via GitHub API
- **🧠 AI-Powered Analysis**: Use OpenAI API for intelligent categorization and relationship analysis
- **📊 Data Export**: Support multiple formats for exporting your star data
- **🌐 Internationalization**: Multi-language interface support
- **🔄 Auto Sync**: Support for automatic periodic updates via Actions

## 🛠️ Quick Start

1. Clone this repository
2. Add the following secrets under `Settings > Secrets and variables > Actions > Repository secrets`:
   - `LANGUAGE`: Set language, supports the following options:
     - `en`: English
     - `zh-CN`: Simplified Chinese
     - `zh-TW`: Traditional Chinese
     - `es`: Spanish
     - `ja`: Japanese
     - `fr`: French
     - `de`: German
     - `ru`: Russian
   - `OPENAI_KEY`: Your OpenAI API key
   Optionally add the following variables under `Repository variables`:
   - `OPENAI_BASE_URL`: OpenAI-compatible API base URL
   - `OPENAI_MODEL`: OpenAI-compatible API model name, defaults to `gpt-5.4-mini`
3. At the bottom of `Settings > Actions > General`, switch `Workflow permissions` to `Read and write permissions` and save

## 🛠️ Local Development

Stars uses uv as the Python package manager. Ensure you have Python 3.11+ installed, then follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/lileyzhao/stars.git
cd stars/src
```

2. Run the program (uv will automatically install dependencies):

```bash
uv run main.py
```

## 📝 Template

- [template README](templates/README.md)

## 📋 Tech Stack

- Python 3.11+
- OpenAI API
- GitHub API
- Rich CLI
- Pandas
- Jinja2

## 💡 Why Stars?

In the endless universe of code, we often mark shining stars (projects), only to get lost in this sea of stars as their numbers grow. Stars was born to solve this problem, helping developers rediscover and organize their collected knowledge, giving meaning to each star and forming their own knowledge galaxy.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lileyzhao/stars&type=Date)](https://www.star-history.com/#lileyzhao/stars&Date)

---
