import {spawnSync} from 'node:child_process';
import {existsSync, readFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const frontendDir = resolve(rootDir, 'frontend');
const backendDir = resolve(rootDir, 'backend');

const packages = {
    python: {
        displayName: 'orcestr-auth',
        kind: 'python',
        manifest: resolve(backendDir, 'pyproject.toml'),
        tagPrefix: 'python-v',
        trackedFiles: ['backend/pyproject.toml', 'backend/uv.lock'],
    },
    core: npmPackage('core', '@orcestr/auth-core', 'auth-core-v'),
    react: npmPackage('react', '@orcestr/auth-react', 'auth-react-v'),
    forms: npmPackage('forms', '@orcestr/auth-forms', 'auth-forms-v'),
    next: npmPackage('next', '@orcestr/auth-next', 'auth-next-v'),
};

class ReleaseError extends Error {}

function npmPackage(directory, displayName, tagPrefix) {
    return {
        displayName,
        kind: 'npm',
        manifest: resolve(frontendDir, 'packages', directory, 'package.json'),
        tagPrefix,
        trackedFiles: [
            `frontend/packages/${directory}/package.json`,
            'frontend/package-lock.json',
        ],
    };
}

function runCommand(command, args, options = {}) {
    const result = spawnSync(command, args, {
        cwd: options.cwd ?? rootDir,
        encoding: 'utf8',
        shell: options.shell ?? false,
        stdio: options.captureOutput ? 'pipe' : 'inherit',
    });

    if (result.error) {
        throw new ReleaseError(result.error.message);
    }

    if (result.status !== 0 && options.check !== false) {
        throw new ReleaseError(`${command} ${args.join(' ')} failed`);
    }

    return result;
}

function git(args, options = {}) {
    return runCommand('git', args, options);
}

function npm(args, options = {}) {
    const npmCliPath = findNpmCli();

    if (npmCliPath) {
        return runCommand(process.execPath, [npmCliPath, ...args], options);
    }

    return runCommand(process.platform === 'win32' ? 'npm.cmd' : 'npm', args, {
        ...options,
        shell: process.platform === 'win32',
    });
}

function findNpmCli() {
    const candidates = [
        process.env.npm_execpath,
        process.platform === 'win32'
            ? resolve(dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js')
            : resolve(dirname(process.execPath), '../lib/node_modules/npm/bin/npm-cli.js'),
    ].filter(Boolean);

    return candidates.find((path) => existsSync(path));
}

function uv(args, options = {}) {
    return runCommand(process.platform === 'win32' ? 'uv.exe' : 'uv', args, options);
}

function readVersion(config) {
    if (config.kind === 'npm') {
        return JSON.parse(readFileSync(config.manifest, 'utf8')).version;
    }

    const pyproject = readFileSync(config.manifest, 'utf8');
    const projectSection = pyproject.match(/\[project\]\s+([\s\S]*?)(?=\n\[|$)/u)?.[1];
    const version = projectSection?.match(/^version\s*=\s*"([^"]+)"/mu)?.[1];

    if (!version) {
        throw new ReleaseError('Could not read [project].version from backend/pyproject.toml.');
    }

    return version;
}

function bumpVersion(version, part) {
    const match = /^(\d+)\.(\d+)\.(\d+)$/u.exec(version);

    if (!match) {
        throw new ReleaseError(`Unsupported stable package version: ${version}`);
    }

    const [, majorText, minorText, patchText] = match;
    const major = Number.parseInt(majorText, 10);
    const minor = Number.parseInt(minorText, 10);
    const patch = Number.parseInt(patchText, 10);

    if (part === 'patch') {
        return `${major}.${minor}.${patch + 1}`;
    }

    if (part === 'minor') {
        return `${major}.${minor + 1}.0`;
    }

    if (part === 'major') {
        return `${major + 1}.0.0`;
    }

    throw new ReleaseError(`Unsupported release part: ${part}`);
}

function checkWorktreeIsClean() {
    const result = git(['status', '--short'], {captureOutput: true});

    if (result.stdout.trim()) {
        throw new ReleaseError('Git worktree is not clean. Commit or stash changes before release.');
    }
}

function checkTagDoesNotExist(tagName) {
    const result = git(['rev-parse', '-q', '--verify', `refs/tags/${tagName}`], {
        captureOutput: true,
        check: false,
    });

    if (result.status === 0) {
        throw new ReleaseError(`Git tag ${tagName} already exists.`);
    }
}

function writeVersion(target, config, part) {
    if (config.kind === 'python') {
        uv(['version', '--bump', part, '--no-sync'], {cwd: backendDir});
        return;
    }

    npm(
        [
            'version',
            part,
            '--workspace',
            config.displayName,
            '--no-git-tag-version',
            '--ignore-scripts',
        ],
        {cwd: frontendDir},
    );
}

function release(target, part, options) {
    const config = packages[target];

    if (!config) {
        throw new ReleaseError(`Unsupported package: ${target}`);
    }

    const currentVersion = readVersion(config);
    const nextVersion = bumpVersion(currentVersion, part);
    const tagName = `${config.tagPrefix}${nextVersion}`;

    console.log(`Package: ${config.displayName}`);
    console.log(`Current version: ${currentVersion}`);
    console.log(`Next version: ${nextVersion}`);
    console.log(`Tag: ${tagName}`);

    if (options.dryRun) {
        console.log('Dry run mode. No files or git objects were changed.');
        return;
    }

    checkWorktreeIsClean();
    checkTagDoesNotExist(tagName);
    writeVersion(target, config, part);

    const writtenVersion = readVersion(config);
    if (writtenVersion !== nextVersion) {
        throw new ReleaseError(
            `Version command wrote ${writtenVersion}, expected ${nextVersion}.`,
        );
    }

    git(['add', ...config.trackedFiles]);
    git(['commit', '-m', `chore: release ${config.displayName} ${tagName}`]);
    git(['tag', '-a', tagName, '-m', `${config.displayName} ${nextVersion}`]);

    if (options.push) {
        git(['push']);
        git(['push', 'origin', tagName]);
        console.log(`Release ${tagName} was pushed.`);
        return;
    }

    console.log('Release commit and tag were created locally.');
    console.log('Run these commands when you are ready to publish:');
    console.log('  git push');
    console.log(`  git push origin ${tagName}`);
}

function main() {
    const [, , target, part, ...flags] = process.argv;
    const allowedTargets = new Set(Object.keys(packages));
    const allowedParts = new Set(['patch', 'minor', 'major']);

    if (!allowedTargets.has(target) || !allowedParts.has(part)) {
        throw new ReleaseError(
            'Usage: node scripts/release.mjs <python|core|react|forms|next> '
                + '<patch|minor|major> [--push] [--dry-run]',
        );
    }

    release(target, part, {
        dryRun: flags.includes('--dry-run'),
        push: flags.includes('--push'),
    });
}

try {
    main();
} catch (error) {
    console.error(`Release error: ${error.message}`);
    process.exit(1);
}
