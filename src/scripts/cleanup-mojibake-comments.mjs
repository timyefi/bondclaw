#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import ts from 'typescript';

const DEFAULT_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.mts', '.cts', '.mjs', '.cjs']);
const IGNORE_DIRS = new Set(['.git', 'node_modules', 'dist', 'out', 'build', 'coverage', '.next', '.turbo']);

const MOJIBAKE_MARKERS =
  /[鍒鍐鍔鍙鍚鍛鍜鍝鍞鍟鍠鍡鍢鍣鍤鍥鍧鍩鍪鍫鍬鍭鍮鍯鍰鍱鍲鍳鍴鍵鍶鍷鍸鍹鍺鍻鍼鍽鍾鍿閫閬閮閯閰閱閳閴閵閶闂璇诲绗彿鐩锛€鏄绯缁璁鎴妯浠鏍绛鑾]/u;
const CJK_RE = /\p{Script=Han}/gu;
const ASCII_RE = /[A-Za-z]/;
const WS_ONLY_RE = /^\s*$/;

function parseArgs(argv) {
  const options = {
    root: process.cwd(),
    write: false,
    deleteOrphan: false,
    verbose: false,
    extensions: new Set(DEFAULT_EXTENSIONS),
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--write') {
      options.write = true;
      continue;
    }
    if (arg === '--delete-orphan-comments') {
      options.deleteOrphan = true;
      continue;
    }
    if (arg === '--verbose') {
      options.verbose = true;
      continue;
    }
    if (arg === '--root') {
      options.root = path.resolve(argv[i + 1] ?? options.root);
      i += 1;
      continue;
    }
    if (arg === '--ext') {
      const ext = argv[i + 1];
      if (ext) {
        options.extensions = new Set(
          ext
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean)
            .map((item) => (item.startsWith('.') ? item : `.${item}`))
        );
      }
      i += 1;
      continue;
    }
    if (!arg.startsWith('--')) {
      options.root = path.resolve(arg);
    }
  }

  return options;
}

function isProbablyMojibake(text) {
  if (!text) return false;
  const hanMatches = text.match(CJK_RE) ?? [];
  if (hanMatches.length === 0) return false;
  return text.includes('�') || text.includes('�?') || MOJIBAKE_MARKERS.test(text);
}

function stripLineCommentPrefix(text) {
  const match = text.match(/^(\s*\/\/\s?)([\s\S]*)$/);
  if (!match) return null;
  return { prefix: match[1], body: match[2], suffix: '' };
}

function stripBlockCommentPrefix(text) {
  const match = text.match(/^(\/\*\*?)([\s\S]*?)(\*\/)$/);
  if (!match) return null;
  return { prefix: match[1], body: match[2], suffix: match[3] };
}

function cleanupLineBody(body, { deleteOrphan }) {
  const segments = body.split(/\s+\/\s+/);
  if (segments.length >= 2) {
    const kept = segments.filter((segment) => !isProbablyMojibake(segment));
    const removed = segments.length - kept.length;
    if (removed > 0 && kept.length > 0) {
      return {
        changed: true,
        newBody: kept.join(' / ').trim(),
        reason: 'removed bilingual mojibake segment',
      };
    }
  }

  if (deleteOrphan && isProbablyMojibake(body) && !ASCII_RE.test(body)) {
    return {
      changed: true,
      newBody: '',
      reason: 'removed orphan mojibake comment',
    };
  }

  return { changed: false, newBody: body, reason: '' };
}

function cleanupBlockBody(body, options) {
  const lines = body.split('\n');
  let changed = false;
  let reason = '';
  const cleanedLines = lines.map((line) => {
    const starMatch = line.match(/^(\s*\*\s?)(.*)$/);
    if (starMatch) {
      const cleanup = cleanupLineBody(starMatch[2], options);
      if (cleanup.changed) {
        changed = true;
        reason ||= cleanup.reason;
        return cleanup.newBody ? `${starMatch[1]}${cleanup.newBody}` : starMatch[1].trimEnd();
      }
      return line;
    }

    const cleanup = cleanupLineBody(line, options);
    if (cleanup.changed) {
      changed = true;
      reason ||= cleanup.reason;
      return cleanup.newBody;
    }
    return line;
  });

  return {
    changed,
    newBody: cleanedLines.join('\n'),
    reason,
  };
}

function rebuildComment(originalText, cleanedBody) {
  const line = stripLineCommentPrefix(originalText);
  if (line) {
    if (WS_ONLY_RE.test(cleanedBody)) return '';
    return `${line.prefix}${cleanedBody}`;
  }

  const block = stripBlockCommentPrefix(originalText);
  if (block) {
    if (WS_ONLY_RE.test(cleanedBody)) return '';
    return `${block.prefix}${cleanedBody}${block.suffix}`;
  }

  return originalText;
}

function collectCommentRanges(sourceText) {
  const comments = [];
  const scanner = ts.createScanner(ts.ScriptTarget.Latest, false, ts.LanguageVariant.Standard, sourceText);

  let token = scanner.scan();
  while (token !== ts.SyntaxKind.EndOfFileToken) {
    if (token === ts.SyntaxKind.SingleLineCommentTrivia || token === ts.SyntaxKind.MultiLineCommentTrivia) {
      comments.push({
        pos: scanner.getTokenPos(),
        end: scanner.getTextPos(),
        text: scanner.getTokenText(),
      });
    }
    token = scanner.scan();
  }

  return comments;
}

function applyReplacements(sourceText, replacements) {
  let result = '';
  let cursor = 0;
  for (const replacement of replacements) {
    result += sourceText.slice(cursor, replacement.pos);
    result += replacement.text;
    cursor = replacement.end;
  }
  result += sourceText.slice(cursor);
  return result;
}

async function walk(dir, extensions, files = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!IGNORE_DIRS.has(entry.name)) {
        await walk(fullPath, extensions, files);
      }
      continue;
    }

    if (entry.isFile() && extensions.has(path.extname(entry.name))) {
      files.push(fullPath);
    }
  }
  return files;
}

async function processFile(filePath, options) {
  const sourceText = await fs.readFile(filePath, 'utf8');
  const comments = collectCommentRanges(sourceText);
  const replacements = [];
  const changes = [];

  for (const comment of comments) {
    const line = stripLineCommentPrefix(comment.text);
    const block = line ? null : stripBlockCommentPrefix(comment.text);
    const cleanup = line
      ? cleanupLineBody(line.body, options)
      : block
        ? cleanupBlockBody(block.body, options)
        : { changed: false, newBody: comment.text, reason: '' };
    if (!cleanup.changed) continue;

    const newComment = rebuildComment(comment.text, cleanup.newBody);
    if (newComment === comment.text) continue;

    replacements.push({ pos: comment.pos, end: comment.end, text: newComment });
    changes.push({ before: comment.text, after: newComment, reason: cleanup.reason });
  }

  if (replacements.length === 0) {
    return { changed: false, filePath, changeCount: 0, changes: [] };
  }

  const nextText = applyReplacements(sourceText, replacements);
  if (nextText !== sourceText && options.write) {
    await fs.writeFile(filePath, nextText, 'utf8');
  }

  return {
    changed: nextText !== sourceText,
    filePath,
    changeCount: changes.length,
    changes,
  };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const stat = await fs.stat(options.root);
  const files = stat.isDirectory() ? await walk(options.root, options.extensions) : [options.root];

  let changedFiles = 0;
  let totalChanges = 0;

  for (const filePath of files) {
    const result = await processFile(filePath, options);
    if (!result.changed) continue;

    changedFiles += 1;
    totalChanges += result.changeCount;

    console.log(
      `${options.write ? 'UPDATED' : 'WOULD UPDATE'} ${path.relative(options.root, filePath) || path.basename(filePath)} (${result.changeCount})`
    );
    if (options.verbose) {
      for (const change of result.changes.slice(0, 5)) {
        console.log(`  - ${change.reason}`);
        console.log(`    before: ${JSON.stringify(change.before)}`);
        console.log(`    after : ${JSON.stringify(change.after)}`);
      }
      if (result.changes.length > 5) {
        console.log(`  ... and ${result.changes.length - 5} more changes`);
      }
    }
  }

  console.log(
    `\nScanned ${files.length} files, ${options.write ? 'updated' : 'would update'} ${changedFiles} files, ${totalChanges} comment changes.`
  );
  if (!options.write) {
    console.log('Dry run only. Re-run with --write to apply changes.');
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
