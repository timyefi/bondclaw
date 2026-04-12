#!/usr/bin/env python3
"""Batch restore corrupted files from upstream AionUi repository."""
import os, sys, urllib.request, time

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://raw.githubusercontent.com/iOfficeAI/AionUi/master/'
SRC_DIR = 'src'

def find_corrupted_files():
    """Find all .ts files that can't be decoded as UTF-8."""
    corrupted = []
    for root, dirs, files in os.walk(SRC_DIR):
        for fname in files:
            if not fname.endswith('.ts'):
                continue
            fp = os.path.join(root, fname)
            try:
                with open(fp, 'rb') as f:
                    raw = f.read()
                raw.decode('utf-8')
            except UnicodeDecodeError:
                rel = fp.replace(os.sep, '/')
                corrupted.append(rel)
    return corrupted

def download_and_replace(rel_path):
    """Download file from upstream and write locally with BondClaw header."""
    url = BASE_URL + rel_path
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'BondClaw-UpstreamSync/1.0')
    with urllib.request.urlopen(req, timeout=20) as resp:
        content = resp.read().decode('utf-8')
    content = content.replace(
        'Copyright 2025 AionUi (aionui.com)',
        'Copyright 2025 BondClaw (github.com/timyefi/bondclaw)'
    )
    with open(rel_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    return content.count('\n')

def main():
    corrupted = find_corrupted_files()
    print(f'Found {len(corrupted)} files with binary corruption (decode_error)')

    success = 0
    failed = 0
    for i, rel_path in enumerate(corrupted):
        try:
            lines = download_and_replace(rel_path)
            success += 1
            if (i + 1) % 20 == 0 or i == len(corrupted) - 1:
                print(f'  [{i+1}/{len(corrupted)}] Replaced {rel_path} ({lines} lines)')
        except urllib.error.HTTPError as e:
            failed += 1
            print(f'  [{i+1}/{len(corrupted)}] HTTP {e.code}: {rel_path}')
        except Exception as e:
            failed += 1
            print(f'  [{i+1}/{len(corrupted)}] ERROR: {rel_path}: {e}')

        # Small delay to avoid rate limiting
        if (i + 1) % 50 == 0:
            time.sleep(0.5)

    print(f'\nDone: {success} replaced, {failed} failed out of {len(corrupted)}')

if __name__ == '__main__':
    main()
