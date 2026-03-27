---
name: mineru
description: "Parse PDFs, Word docs, PPTs, and images into clean Markdown using MinerU's VLM engine. Use when: (1) Converting PDF/Word/PPT/image to Markdown, (2) Extracting text/tables/formulas from documents, (3) Batch processing multiple files, (4) Saving parsed content to Obsidian or knowledge bases. Supports LaTeX formulas, tables, images, multilingual OCR, and async parallel processing."
homepage: https://mineru.net
metadata:
  openclaw:
    emoji: "📄"
    requires:
      bins: ["python3"]
      env:
        - name: MINERU_TOKEN
          description: "MinerU API key — get free token at https://mineru.net/user-center/api-token (2000 pages/day, 200MB/file)"
    install:
      - id: pip
        kind: pip
        packages: ["requests", "aiohttp"]
        label: "Install Python dependencies (pip)"
---

# MinerU Document Parser

Convert PDF, Word, PPT, and images to clean Markdown using MinerU's VLM engine — LaTeX formulas, tables, and images all preserved.

## Setup

1. Get free API token at https://mineru.net/user-center/api-token
2. API Token 已配置在 `config.json` 文件中（首次使用请编辑更新）

**Limits:** 2000 pages/day · 200 MB per file · 600 pages per file

## Execution Norms (Mandatory) - 唯一执行方式

This skill **MUST** be executed through **Python subprocess** only. No other execution method is allowed.

### ⚠️ MANDATORY: Only This Execution Method

| Method | Allowed |
|--------|---------|
| `python3 scripts/mineru.py ...` | ❌ FORBIDDEN |
| `python scripts/mineru.py ...` | ❌ FORBIDDEN |
| `subprocess.Popen([sys.executable, 'mineru.py', ...])` + 日志轮询 | ✅ ONLY |

### Background Execution with Logging (Mandatory)

```python
import subprocess
import sys
import time
import os
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SKILL_DIR = r'C:\Users\Administrator\.workbuddy\skills\mineru-skill'
CONFIG_FILE = os.path.join(SKILL_DIR, 'config.json')

# 1. 自动加载 config.json 中的 token
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)
os.environ['MINERU_TOKEN'] = config.get('token', '')

# 2. 配置参数
script = os.path.join(SKILL_DIR, 'scripts', 'mineru_stable.py')
input_path = r'C:\path\to\your\file.pdf'  # 替换为实际文件
output_dir = r'c:\temp\mineru_output'
log_file = r'c:\temp\mineru.log'

# 3. 启动后台进程 (mineru_stable.py 不支持 --workers)
process = subprocess.Popen(
    [sys.executable, script,
     '--file', input_path,
     '--output', output_dir,
     '--language', 'ch'],
    stdout=open(log_file, 'w', encoding='utf-8'),
    stderr=subprocess.STDOUT,
    text=True,
    cwd=os.path.dirname(script)
)

print(f"后台任务启动, PID: {process.pid}")

# 4. 轮询检查日志 (每15秒)
max_wait = 3600
interval = 15
elapsed = 0

while elapsed < max_wait:
    time.sleep(interval)
    elapsed += interval
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.strip().split('\n')
            print(f"[{elapsed}秒] {lines[-1] if lines else '...'}")
            
            if '✅ 成功:' in content:
                print("任务完成!")
                break
            if '❌ 失败:' in content:
                print("任务失败")
                break
    except FileNotFoundError:
        pass
```

### 3. Progress Keywords

Check log files for progress:

| Keyword | Meaning |
|---------|---------|
| `开始处理 N 个文件` | Task started |
| `正在处理:` | Processing in progress |
| `成功:` | Completed successfully |
| `失败:` | Task failed |

---

## Supported File Types

| Type | Formats |
|------|---------|
| 📕 PDF | `.pdf` — papers, textbooks, scanned docs |
| 📝 Word | `.docx` — reports, manuscripts |
| 📊 PPT | `.pptx` — slides, presentations |
| 🖼️ Image | `.jpg`, `.jpeg`, `.png` — OCR extraction |

## Commands

All command execution **MUST** use Python subprocess pattern. See Execution Norms section for details.

### Script Parameters

| Parameter | Description | Supported Scripts |
|-----------|-------------|-------------------|
| `--dir PATH` | Input directory (PDF/Word/PPT/images) | All |
| `--file PATH` | Single file | All |
| `--output PATH` | Output directory (default: `./output/`) | All |
| `--workers N` | Concurrent workers (default: 5, max: 15) | **mineru_v2.py only** |
| `--resume` | Skip already processed files | All |
| `--model MODEL` | Model version: pipeline / vlm / MinerU-HTML (default: vlm) | All |
| `--language LANG` | Document language: auto / en / ch (default: auto) | All |
| `--token TOKEN` | API token (overrides MINERU_TOKEN env var) | All |

> **⚠️ 重要**：`--workers` 参数仅 `mineru_v2.py` 支持。`mineru_stable.py` 是串行版本，不支持此参数。

## CLI Options

### mineru_v2.py (并行版本)
```
--dir PATH          Input directory (PDF/Word/PPT/images)
--file PATH         Single file
--output PATH       Output directory (default: ./output/)
--workers N         Concurrent workers (default: 5, max: 15)
--resume            Skip already processed files
--model MODEL       Model version: pipeline | vlm | MinerU-HTML (default: vlm)
--language LANG     Document language: auto | en | ch (default: auto)
--no-formula        Disable formula recognition
--no-table          Disable table extraction
--token TOKEN       API token (overrides MINERU_TOKEN env var)
```

### mineru_stable.py (串行版本)
```
--dir PATH          Input directory (PDF/Word/PPT/images)
--file PATH         Single file
--output PATH       Output directory (default: ./output/)
--resume            Skip already processed files
--model MODEL       Model version: pipeline | vlm | MinerU-HTML (default: vlm)
--language LANG     Document language: auto | en | ch (default: auto)
--no-formula        Disable formula recognition
--no-table          Disable table extraction
--token TOKEN       API token (overrides MINERU_TOKEN env var)
```

> **注意**：`mineru_stable.py` 不支持 `--workers` 参数

## Model Version Guide

| Model | Speed | Accuracy | Best For |
|-------|-------|----------|----------|
| `pipeline` | ⚡ Fast | High | Standard docs, most use cases |
| `vlm` | 🐢 Slow | Highest | Complex layouts, multi-column, mixed text+figures |
| `MinerU-HTML` | ⚡ Fast | High | Web-style output, HTML-ready content |

## Script Selection

| Script | Workers | Use When |
|--------|---------|----------|
| `mineru_v2.py` | ✅ 支持 (1-15) | Default — 并行处理，适合多文件批量 |
| `mineru_stable.py` | ❌ 不支持 | Unstable network — 串行处理，单文件更稳定 |

> **选择建议**：多文件批量处理用 `mineru_v2.py` + `--workers 5`；网络不稳定或单文件用 `mineru_stable.py`

## Output Structure

```
output/
├── document-name/
│   ├── document-name.md    # Main Markdown
│   ├── images/             # Extracted images
│   └── content.json        # Metadata
```

## Performance

| Workers | Speed |
|---------|-------|
| 1 (sequential) | 1.2 files/min |
| 5 | 3.1 files/min |
| 15 | 5.6 files/min |

## Error Handling

- 5x auto-retry with exponential backoff
- Use `--resume` to continue interrupted batches
- Failed files listed at end of run

## API Reference

For detailed API documentation, see [references/api_reference.md](references/api_reference.md).
