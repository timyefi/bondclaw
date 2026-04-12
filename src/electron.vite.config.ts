import { defineConfig, externalizeDepsPlugin } from 'electron-vite';
import { execSync } from 'child_process';
import { resolve } from 'path';
import { sentryVitePlugin } from '@sentry/vite-plugin';
import UnoCSS from 'unocss/vite';
import unoConfig from './uno.config.ts';
import { viteStaticCopy } from 'vite-plugin-static-copy';

// Build builtin MCP servers after the main process bundle so they survive out/main/ cleanup.
function buildMcpServersPlugin() {
  return {
    name: 'vite-plugin-build-mcp-servers',
    closeBundle() {
      execSync(`node "${resolve('scripts/build-mcp-servers.js')}"`, { stdio: 'inherit' });
    },
  };
}

// Icon Park transform plugin (replaces webpack icon-park-loader)
function iconParkPlugin() {
  return {
    name: 'vite-plugin-icon-park',
    enforce: 'pre' as const,
    transform(source: string, id: string) {
      if (!id.endsWith('.tsx') || id.includes('node_modules')) return null;
      if (!source.includes('@icon-park/react')) return null;
      const transformedSource = source.replace(
        /import\s+\{\s+([a-zA-Z, ]*)\s+\}\s+from\s+['"]@icon-park\/react['"](;?)/g,
        function (str, match) {
          if (!match) return str;
          const components = match.split(',');
          const importComponent = str.replace(
            match,
            components.map((key: string) => `${key} as _${key.trim()}`).join(', ')
          );
          const hoc = `import IconParkHOC from '@renderer/components/IconParkHOC';
          ${components.map((key: string) => `const ${key.trim()} = IconParkHOC(_${key.trim()})`).join(';\n')}`;
          return importComponent + ';' + hoc;
        }
      );
      if (transformedSource !== source) return { code: transformedSource, map: null } as { code: string; map: null };
      return null;
    },
  };
}

// Common path aliases for main process and workers
const mainAliases = {
  '@': resolve('src'),
  '@common': resolve('src/common'),
  '@renderer': resolve('src/renderer'),
  '@process': resolve('src/process'),
  '@worker': resolve('src/process/worker'),
  '@xterm/headless': resolve('src/common/utils/shims/xterm-headless.ts'),
};

export default defineConfig(({ mode }) => {
  const isDevelopment = mode === 'development';
  const enableSentrySourceMaps = !isDevelopment && !!process.env.SENTRY_AUTH_TOKEN;

  const sentryPluginOptions = {
    org: process.env.SENTRY_ORG,
    project: process.env.SENTRY_PROJECT,
    authToken: process.env.SENTRY_AUTH_TOKEN,
    sourcemaps: {
      filesToDeleteAfterUpload: ['./out/**/*.map'],
      rewriteSources: (source: string) => {
        // Normalize Windows backslashes and strip leading relative prefixes
        // so Sentry paths match the GitHub repo structure (e.g. src/process/...).
        return source.replace(/\\/g, '/').replace(/^(\.\.\/)+(src\/)/, '$2');
      },
    },
  };

  return {
    main: {
      plugins: [
        // externalizeDepsPlugin replaces our custom getExternalDeps() + pluginExternalizeDynamicImports.
        // 'fix-path' excluded so it gets bundled inline (only 3KB).
        externalizeDepsPlugin({ exclude: ['fix-path'] }),
        ...(isDevelopment
          ? [
              {
                name: 'dev-build-mcp-servers',
                closeBundle() {
                  execSync(`node "${resolve(__dirname, 'scripts/build-mcp-servers.js')}"`, {
                    stdio: 'inherit',
                  });
                },
              },
            ]
          : []),
        ...(!isDevelopment
          ? [
              viteStaticCopy({
                structured: false,
                // electron-vite builds main process as SSR; viteStaticCopy defaults
                // to environment: "client" and silently skips non-client environments.
                environment: 'ssr',
                targets: [
                  // Use single * glob to copy top-level items (directories) with their contents intact.
                  // Using ** would flatten all nested files into the dest root.
                  { src: 'src/process/resources/skills/*', dest: 'skills' },
                  { src: 'src/process/resources/assistant/*', dest: 'assistant' },
                  { src: 'src/renderer/assets/logos/*', dest: 'static/images' },
                  // BondClaw prompt library and research brain data
                  { src: '../prompt-library/packs/*', dest: 'bondclaw-prompts' },
                  { src: '../research-brain/*', dest: 'bondclaw-research-brain' },
                ],
              }),
            ]
          : []),
        ...(enableSentrySourceMaps ? [sentryVitePlugin(sentryPluginOptions)] : []),
        ...(isDevelopment ? [buildMcpServersPlugin()] : []),
      ],
      resolve: { alias: mainAliases, extensions: ['.ts', '.tsx', '.js', '.json'] },
      build: {
        sourcemap: enableSentrySourceMaps ? 'hidden' : false,
        reportCompressedSize: false,
        rollupOptions: {
          input: {
            index: resolve('src/index.ts'),
          },
          onwarn(warning, warn) {
            if (warning.code === 'EVAL') return;
            warn(warning);
          },
        },
      },
      define: {
        'process.env.NODE_ENV': JSON.stringify(mode),
        'process.env.env': JSON.stringify(process.env.env),
        'process.env.SENTRY_DSN': JSON.stringify(process.env.SENTRY_DSN ?? ''),
      },
    },

    preload: {
      plugins: [externalizeDepsPlugin()],
      resolve: {
        alias: { '@': resolve('src'), '@common': resolve('src/common') },
        extensions: ['.ts', '.tsx', '.js', '.json'],
      },
      build: {
        sourcemap: false,
        reportCompressedSize: false,
        rollupOptions: {
          input: {
            index: resolve('src/preload/main.ts'),
            petPreload: resolve('src/preload/petPreload.ts'),
            petHitPreload: resolve('src/preload/petHitPreload.ts'),
            petConfirmPreload: resolve('src/preload/petConfirmPreload.ts'),
          },
        },
      },
      define: {
        'process.env.NODE_ENV': JSON.stringify(mode),
        'process.env.env': JSON.stringify(process.env.env),
        'process.env.AIONUI_MULTI_INSTANCE': JSON.stringify(process.env.AIONUI_MULTI_INSTANCE ?? ''),
        'process.env.SENTRY_DSN': JSON.stringify(process.env.SENTRY_DSN ?? ''),
        global: 'globalThis',
      },
      optimizeDeps: {
        exclude: ['electron'],
        include: [
          'react',
          'react-dom',
          'react-router-dom',
          'react-i18next',
          'i18next',
          '@arco-design/web-react',
          '@icon-park/react',
          'react-markdown',
          'react-syntax-highlighter',
          'react-virtuoso',
          'classnames',
          'swr',
          'eventemitter3',
          'katex',
          'diff2html',
          'remark-gfm',
          'remark-math',
          'remark-breaks',
          'rehype-raw',
          'rehype-katex',
        ],
      },
    },

    renderer: {
      base: './',
      publicDir: resolve('public'),
      appType: 'mpa',
      server: {
        port: 5173,
        hmr: {
          host: 'localhost',
        },
      },
      resolve: {
        alias: {
          '@': resolve('src'),
          '@common': resolve('src/common'),
          '@renderer': resolve('src/renderer'),
          '@process': resolve('src/process'),
          '@worker': resolve('src/process/worker'),
          streamdown: resolve('node_modules/streamdown/dist/index.js'),
        },
        extensions: ['.ts', '.tsx', '.js', '.jsx', '.css'],
        dedupe: ['react', 'react-dom', 'react-router-dom'],
      },
      plugins: [
        UnoCSS(unoConfig),
        iconParkPlugin(),
        ...(enableSentrySourceMaps ? [sentryVitePlugin(sentryPluginOptions)] : []),
      ],
      build: {
        target: 'es2022',
        sourcemap: enableSentrySourceMaps ? 'hidden' : isDevelopment,
        minify: !isDevelopment,
        reportCompressedSize: false,
        chunkSizeWarningLimit: 1500,
        cssCodeSplit: true,
        rollupOptions: {
          input: {
            index: resolve('src/renderer/index.html'),
            pet: resolve('src/renderer/pet/pet.html'),
            'pet-hit': resolve('src/renderer/pet/pet-hit.html'),
            'pet-confirm': resolve('src/renderer/pet/pet-confirm.html'),
          },
          external: ['node:crypto', 'crypto'],
        },
      },
      define: {
        'process.env.NODE_ENV': JSON.stringify(mode),
        'process.env.env': JSON.stringify(process.env.env),
        'process.env.AIONUI_MULTI_INSTANCE': JSON.stringify(process.env.AIONUI_MULTI_INSTANCE ?? ''),
        'process.env.SENTRY_DSN': JSON.stringify(process.env.SENTRY_DSN ?? ''),
      },
    },
  };
});
