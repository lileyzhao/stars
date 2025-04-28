<div align="center">

# 🌟 {{ title }} 🌟

{{ slogan }}

[![GitHub Stars](https://img.shields.io/badge/GitHub%20Stars-{{ github_username }}-blue)](https://github.com/{{ github_username }}?tab=stars) [![Last Updated](https://img.shields.io/badge/Last%20Updated-{{ generated_at }}-blue)](https://github.com/{{ github_username }}/stars) [![Powered by](https://img.shields.io/badge/Powered%20by-@lileyzhao/stars-green)](https://github.com/lileyzhao/stars/tree/main/docs)

</div>

---

## 📚 {{ table_of_contents }}
{% for category, repos in groups.items() %}
{%- set subcategories = [] %}
{%- for repo in repos %}
{%- if repo.subcategory and repo.subcategory not in subcategories %}
{%- set _ = subcategories.append(repo.subcategory) %}
{%- endif %}
{%- endfor %}
• **[{{ category }}](#{{ category|replace(' ', '-') }})** - {% for subcategory in subcategories %}[{{ subcategory }}](#{{ subcategory|replace(' ', '-') }}){% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}
---

{% for category, repos in groups.items() -%}
## • {{ category }}
{%- set subcategory_groups = {} -%}
{%- for repo in repos -%}
{%- if repo.subcategory not in subcategory_groups -%}
{%- set _ = subcategory_groups.update({repo.subcategory: []}) -%}
{%- endif -%}
{%- set _ = subcategory_groups[repo.subcategory].append(repo) -%}
{%- endfor -%}
{%- for subcategory, subcategory_repos in subcategory_groups.items() -%}
{%- if subcategory %}

### ◦ {{ subcategory }}
{%- endif -%}
{%- for repo in subcategory_repos %}

#### 📦 [{{ repo.full_name }}]({{ repo.html_url }})

[![GitHub stars](https://img.shields.io/github/stars/{{ repo.full_name }}?style=flat-square)]({{ repo.html_url }}/stargazers) [![Top Language](https://img.shields.io/github/languages/top/{{ repo.full_name }}?style=flat-square)]({{ repo.html_url }}) [![Last Commit](https://img.shields.io/github/last-commit/{{ repo.full_name }}?style=flat-square)]({{ repo.html_url }}/commits)

> {{ repo.ai_description }}

🔧 **{{ tech_stack }}:** {{ repo.primary_language }}{% if repo.secondary_language %}, {{ repo.secondary_language }}{% endif %}

{% if repo.topics %}🏷️ **{{ keywords }}:** {{ repo.topics }}{% endif %}
{%- endfor -%}
{%- endfor -%}
{%- endfor %}

---

<div align="center">

## 🚀 {{ about_title }}

{{ about_description }}

{{ about_subtitle }}

[![Star on GitHub](https://img.shields.io/github/stars/lileyzhao/stars?style=social)](https://github.com/lileyzhao/stars/stargazers)

</div>
