const { Arch } = require('builder-util');
const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  normalizeArch,
  rebuildSingleModule,
  verifyModuleBinary,
  getModulesToRebuild,
} = require('./rebuildNativeModules');

/**
 * afterPack hook for electron-builder
 * Rebuilds native modules for cross-architecture builds
 */

module.exports = async function afterPack(context) {
  const { arch, electronPlatformName, appOutDir, packager } = context;
  const targetArch = normalizeArch(typeof arch === 'string' ? arch : Arch[arch] || process.arch);
  const buildArch = normalizeArch(os.arch());

  console.log(`\n馃敡 afterPack hook started`);
  console.log(`   Platform: ${electronPlatformName}, Build arch: ${buildArch}, Target arch: ${targetArch}`);

  const isCrossCompile = buildArch !== targetArch;
  const forceRebuild = process.env.FORCE_NATIVE_REBUILD === 'true';
  const needsSameArchRebuild = electronPlatformName === 'win32'; // 鍙湁 Windows 闇€瑕佸悓鏋舵瀯閲嶅缓浠ュ尮閰?Electron ABI | Only Windows needs same-arch rebuild to match Electron ABI
  // Linux 浣跨敤棰勭紪璇戜簩杩涘埗锛岄伩鍏?GLIBC 鐗堟湰渚濊禆 | Linux uses prebuilt binaries which are GLIBC-independent

  if (!isCrossCompile && !needsSameArchRebuild && !forceRebuild) {
    console.log(`   鉁?Same architecture, rebuild skipped (set FORCE_NATIVE_REBUILD=true to override)\n`);
    return;
  }

  // Note: Previously there was an optimization to skip macOS cross-compilation,
  // but this caused incorrect architecture binaries (arm64) to be included in x64 builds.
  // Now we always rebuild native modules for cross-compilation to ensure correctness.
  // The rebuild process uses prebuild-install first (fast), falling back to source compilation only when needed.

  if (isCrossCompile) {
    console.log(`   鈿狅笍  Cross-compilation detected (${buildArch} 鈫?${targetArch}), will rebuild native modules`);
    if (electronPlatformName === 'darwin') {
      console.log(`   馃挕 Using prebuild-install for faster cross-architecture build`);
    }
  } else if (needsSameArchRebuild || forceRebuild) {
    console.log(`   鈩癸笍  Rebuilding native modules for platform requirements (force=${forceRebuild})`);
  }

  console.log(`\n馃敡 Checking native modules (${electronPlatformName}-${targetArch})...`);
  console.log(`   appOutDir: ${appOutDir}`);

  const electronVersion =
    packager?.info?.electronVersion ??
    packager?.config?.electronVersion ??
    require('../package.json').devDependencies?.electron?.replace(/^\D*/, '');

  // Determine resources directory based on platform
  // macOS: appOutDir/AionUi.app/Contents/Resources
  // Windows/Linux: appOutDir/resources
  let resourcesDir;
  if (electronPlatformName === 'darwin') {
    const appName = packager?.appInfo?.productFilename || 'AionUi';
    resourcesDir = path.join(appOutDir, `${appName}.app`, 'Contents', 'Resources');
  } else {
    resourcesDir = path.join(appOutDir, 'resources');
  }

  // Debug: check what's in resources directory
  console.log(`   Checking resources directory: ${resourcesDir}`);
  if (fs.existsSync(resourcesDir)) {
    const resourcesContents = fs.readdirSync(resourcesDir);
    console.log(`   Contents: ${resourcesContents.join(', ')}`);

    // Check if app.asar.unpacked exists
    const unpackedDir = path.join(resourcesDir, 'app.asar.unpacked');
    if (fs.existsSync(unpackedDir)) {
      const unpackedContents = fs.readdirSync(unpackedDir);
      console.log(`   app.asar.unpacked contents: ${unpackedContents.join(', ')}`);

      // Check node_modules
      const nodeModulesDir = path.join(unpackedDir, 'node_modules');
      if (fs.existsSync(nodeModulesDir)) {
        const modulesContents = fs.readdirSync(nodeModulesDir);
        console.log(`   node_modules contents: ${modulesContents.slice(0, 10).join(', ')}...`);
      } else {
        console.warn(`   鈿狅笍  node_modules not found in app.asar.unpacked`);
      }
    } else {
      console.warn(`   鈿狅笍  app.asar.unpacked not found`);
    }
  } else {
    console.warn(`鈿狅笍  resources directory not found: ${resourcesDir}`);
    return;
  }

  const nodeModulesDir = path.join(resourcesDir, 'app.asar.unpacked', 'node_modules');

  // Modules that need to be rebuilt for cross-compilation
  // Use platform-specific module list (Windows skips node-pty due to cross-compilation issues)
  const modulesToRebuild = getModulesToRebuild(electronPlatformName);
  console.log(`   Modules to rebuild: ${modulesToRebuild.join(', ')}`);

  // For cross-compilation, clean up build artifacts from the wrong architecture
  // This prevents node-gyp-build from loading incorrect binaries
  if (isCrossCompile) {
    console.log(`\n馃Ч Cleaning up wrong-architecture build artifacts...`);
    for (const moduleName of modulesToRebuild) {
      const moduleRoot = path.join(nodeModulesDir, moduleName);
      if (!fs.existsSync(moduleRoot)) continue;

      // Remove build/ directory (contains wrong-arch compiled binaries)
      const buildDir = path.join(moduleRoot, 'build');
      if (fs.existsSync(buildDir)) {
        fs.rmSync(buildDir, { recursive: true, force: true });
        console.log(`   鉁?Removed ${moduleName}/build/`);
      }

      // Remove bin/ directory (might contain wrong-arch binaries)
      const binDir = path.join(moduleRoot, 'bin');
      if (fs.existsSync(binDir)) {
        fs.rmSync(binDir, { recursive: true, force: true });
        console.log(`   鉁?Removed ${moduleName}/bin/`);
      }
    }

    // Also clean up architecture-specific packages that shouldn't be included
    // Remove packages for the opposite architecture of the target
    const wrongArchSuffix = targetArch === 'arm64' ? 'x64' : 'arm64';
    console.log(`\n馃Ч Removing ${wrongArchSuffix}-specific optional dependencies (target: ${targetArch})...`);

    if (fs.existsSync(nodeModulesDir)) {
      const allModules = fs.readdirSync(nodeModulesDir);
      for (const module of allModules) {
        const modulePath = path.join(nodeModulesDir, module);

        // Handle scoped packages (e.g., @lydell, @napi-rs)
        if (module.startsWith('@') && fs.existsSync(modulePath) && fs.statSync(modulePath).isDirectory()) {
          const scopedPackages = fs.readdirSync(modulePath);
          for (const pkg of scopedPackages) {
            if (pkg.includes(`-${wrongArchSuffix}`) || pkg.includes(`-${electronPlatformName}-${wrongArchSuffix}`)) {
              const pkgPath = path.join(modulePath, pkg);
              if (fs.existsSync(pkgPath) && fs.statSync(pkgPath).isDirectory()) {
                fs.rmSync(pkgPath, { recursive: true, force: true });
                console.log(`   鉁?Removed ${module}/${pkg}`);
              }
            }
          }
        }
        // Handle regular packages
        else if (
          module.includes(`-${wrongArchSuffix}`) ||
          module.includes(`-${electronPlatformName}-${wrongArchSuffix}`)
        ) {
          if (fs.existsSync(modulePath) && fs.statSync(modulePath).isDirectory()) {
            fs.rmSync(modulePath, { recursive: true, force: true });
            console.log(`   鉁?Removed ${module}`);
          }
        }
      }
    }
  }

  const failedModules = [];

  for (const moduleName of modulesToRebuild) {
    const moduleRoot = path.join(nodeModulesDir, moduleName);

    if (!fs.existsSync(moduleRoot)) {
      console.warn(`   鈿狅笍  ${moduleName} not found, skipping`);
      continue;
    }

    console.log(`   鉁?Found ${moduleName}, rebuilding for ${targetArch}...`);

    // For Windows, prefer prebuild-install first (faster and more reliable in CI)
    // electron-rebuild can hang on "Searching dependency tree" in some CI environments
    // prebuild-install will fall back to electron-rebuild internally if no prebuilt binary exists
    const forceRebuildFromSource = false; // Always try prebuild-install first

    const success = rebuildSingleModule({
      moduleName,
      moduleRoot,
      platform: electronPlatformName,
      arch: targetArch,
      electronVersion,
      projectRoot: path.resolve(__dirname, '..'),
      buildArch: buildArch, // Pass build architecture for cross-compile detection
      forceRebuild: forceRebuildFromSource, // Always try prebuild-install first, fallback to rebuild
    });

    if (success) {
      console.log(`     鉁?Rebuild completed`);
    } else {
      console.error(`     鉁?Rebuild failed`);
      failedModules.push(moduleName);
      continue;
    }

    const verified = verifyModuleBinary(moduleRoot, moduleName);
    if (verified) {
      console.log(`     鉁?Binary verification passed`);
    } else {
      console.error(`     鉁?Binary verification failed`);
      failedModules.push(moduleName);
    }

    console.log(''); // Empty line between modules
  }

  if (failedModules.length > 0) {
    throw new Error(`Failed to rebuild modules for ${electronPlatformName}-${targetArch}: ${failedModules.join(', ')}`);
  }

  console.log(`鉁?All native modules rebuilt successfully for ${targetArch}`);

  // ---------------------------------------------------------------------------
  // Force-copy Claude Code seed into resources
  // ---------------------------------------------------------------------------
  // electron-builder respects .gitignore (including `node_modules/`) when
  // processing extraResources, which silently drops the entire node_modules
  // tree from resources/claude-code/.  The afterPack hook runs AFTER
  // electron-builder has finished copying, so we force the copy here.
  // ---------------------------------------------------------------------------
  const claudeSourceDir = path.resolve(__dirname, '..', 'resources', 'claude-code');
  const claudeTargetDir = path.join(resourcesDir, 'claude-code');
  const claudeCliMarker = path.join(
    claudeTargetDir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js'
  );

  if (fs.existsSync(claudeCliMarker)) {
    console.log(`   鉁?Claude Code seed already present, skipping copy.`);
  } else if (fs.existsSync(path.join(claudeSourceDir, 'node_modules'))) {
    console.log(`\n馃搧 Force-copying Claude Code seed (gitignore workaround)...`);
    if (fs.existsSync(claudeTargetDir)) {
      fs.rmSync(claudeTargetDir, { recursive: true, force: true });
    }
    fs.cpSync(claudeSourceDir, claudeTargetDir, { recursive: true, force: true, dereference: true });

    // Quick size check
    let totalSize = 0;
    function walkSize(dir) {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) walkSize(full);
        else totalSize += fs.statSync(full).size;
      }
    }
    walkSize(claudeTargetDir);
    const sizeMb = Math.round(totalSize / 1024 / 1024 * 10) / 10;
    console.log(`   鉁?Claude Code seed copied (${sizeMb} MB)`);

    if (!fs.existsSync(claudeCliMarker)) {
      throw new Error('Claude Code seed copy failed: cli.js not found after copy');
    }
  } else {
    console.warn(`   鈿狅笍  Claude Code seed source not found, skipping.`);
  }

  console.log('');
};
