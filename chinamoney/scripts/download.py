#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChinaMoney 单文件下载入口。"""

from download_support import (  # type: ignore
    cli_main,
    download_file,
    download_file_with_metadata,
    resolve_cninfo_mirror,
    sanitize_filename,
    setup_encoding,
    validate_path,
    validate_url,
)

__all__ = [
    "cli_main",
    "download_file",
    "download_file_with_metadata",
    "resolve_cninfo_mirror",
    "sanitize_filename",
    "setup_encoding",
    "validate_path",
    "validate_url",
]


if __name__ == "__main__":
    raise SystemExit(cli_main())
