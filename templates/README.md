# 星标仓库分析模板

本目录包含用于生成GitHub星标仓库分析报告的模板文件。模板使用Jinja2语法，支持HTML和CSS样式增强，以创建美观的Markdown输出。

## 可用模板

### 1. github.md

默认模板，提供github风格的Markdown格式输出。

## 如何使用

在运行stars工具时，可以通过`--template`参数指定要使用的模板：

```bash
# 使用默认模板
python -m src.main --username <你的GitHub用户名>

# 使用美化版模板
python -m src.main --username <你的GitHub用户名> --template beautiful.md

# 使用现代化模板
python -m src.main --username <你的GitHub用户名> --template modern.md
```

## 自定义模板

你可以基于现有模板创建自己的自定义模板：

1. 复制一个现有模板作为起点
2. 修改HTML/CSS样式和布局
3. 保存为新的`.md`文件
4. 使用`--template`参数指定你的自定义模板

## 模板变量

模板中可以使用以下变量：

- `title`: 报告标题
- `generated_by`: 生成信息
- `groups`: 按类别分组的仓库数据
- `last_updated`: "最后更新时间"的翻译
- `created_at`: "创建时间"的翻译
- `last_pushed`: "最后推送"的翻译
- `license`: "许可证"的翻译
- `topics`: "主题"的翻译
- `github_pages`: "GitHub Pages"的翻译
- `none`: "无"的翻译

## 注意事项

- 模板中的HTML和CSS样式在GitHub上可以正常显示，但在其他Markdown查看器中可能会被忽略
- 为保证最佳兼容性，模板同时提供了基本的Markdown格式和增强的HTML样式
- 暗黑模式样式通过CSS媒体查询自动适配系统设置