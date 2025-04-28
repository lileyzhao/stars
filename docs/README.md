# 🌟 Stars

<img src="https://img.shields.io/badge/status-开发中-brightgreen" alt="状态：开发中"> <img src="https://img.shields.io/badge/版本-0.1.0-blue" alt="版本"> <img src="https://img.shields.io/badge/许可证-MIT-orange" alt="许可证">

> **智能整理你的GitHub星标，发现隐藏的知识星系**

[English](README_EN.md) | [简体中文](README.md)

## 🚀 项目概述

**Stars** 是一个强大的GitHub星标分类整理工具，它利用AI的力量，将你杂乱无章的GitHub星标收藏转化为井然有序的知识宇宙。不再需要手动整理那些随时间积累的数百个项目，让人工智能为你绘制知识星图。

```
"星辰大海中，每一颗星都有自己的故事和归属。"
```

## ✨ 核心功能

- **🔍 GitHub集成**：通过GitHub API自动获取你的所有星标项目
- **🧠 AI智能分析**：使用OpenAI API对项目进行智能分类和关联分析
- **📊 数据导出**：支持多种格式导出你的星标数据
- **🌐 国际化支持**：提供多语言界面
- **🔄 自动同步**：支持Actions定期自动同步更新

## 🛠️ 快速使用

1. 克隆本仓库
2. 在仓库的 `Settings > Secrets and variables > Actions > Repository secrets` 下新增以下变量：
   - `LANGUAGE`: 设置界面语言，支持以下选项：
     - `en`: 英语
     - `zh-CN`: 简体中文
     - `zh-TW`: 繁体中文
     - `es`: 西班牙语
     - `ja`: 日语
     - `fr`: 法语
     - `de`: 德语
     - `ru`: 俄语
   - `OPENAI_KEY`: 你的 OpenAI API 密钥
3. 在 `Settings > Actions > General` 页面底部，将 `Workflow permissions` 切换至 `Read and write permissions` 并保存

## 🛠️ 本地运行

Stars使用uv作为Python包管理工具。确保你安装了Python 3.11+，然后按照以下步骤安装：

1. 克隆仓库：

```bash
git clone https://github.com/lileyzhao/stars.git
cd stars/src
```

2. 运行程序(uv会自动安装依赖)：

```bash
uv run main.py
```

## 📋 技术栈

- Python 3.11+
- OpenAI API
- GitHub API
- Rich CLI
- Pandas
- Jinja2

## 💡 为什么创建Stars？

在无尽的代码宇宙中，我们常常会标记那些闪耀的星星（项目），却在数量增长后迷失在这片星海。Stars正是为解决这个问题而生，它帮助开发者重新理解和组织他们收集的知识，让每一颗星都能被赋予意义，形成自己的知识星系。

## 📃 许可证

MIT © LileyZhao