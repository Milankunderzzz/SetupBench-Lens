import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const projectRoot = path.resolve(import.meta.dirname, '..');
const setupLensRoot = path.resolve(process.env.SETUPLENS_ROOT ?? 'F:/Projects/SetupLens');
const expectedCommit = '424a3307dffd6e1bfaf9b5caca68046f930c790c';
const actualCommit = execFileSync('git', ['-C', setupLensRoot, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
if (actualCommit !== expectedCommit) {
  throw new Error(`SetupLens commit mismatch: expected ${expectedCommit}, got ${actualCommit}`);
}

const manifest = JSON.parse(await fs.readFile(path.join(projectRoot, 'config', 'repositories.frozen.json'), 'utf8'));
const rawRoot = path.join(projectRoot, 'dataset', 'raw');
const reposRoot = path.join(projectRoot, 'dataset', 'repos');
const { scan } = await import(pathToFileURL(path.join(setupLensRoot, 'src', 'scan.js')));
await fs.mkdir(rawRoot, { recursive: true });

function normalize(report, repositoryId) {
  return {
    ...report,
    generatedAt: report.generatedAt,
    target: { ...report.target, path: `<DATASET>/${repositoryId}` },
    experiment: {
      setupLensCommit: expectedCommit,
      repositoryId,
    },
  };
}

for (const [index, repository] of manifest.repositories.entries()) {
  const repositoryPath = path.join(reposRoot, repository.id);
  const report = normalize(await scan(repositoryPath), repository.id);
  const outputPath = path.join(rawRoot, `${repository.id}-setuplens.json`);
  await fs.writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log(
    `[${String(index + 1).padStart(2, '0')}/50] ${repository.id}: ` +
    `${report.primaryStack ?? 'none'}, ${report.scopes.setup.summary.fail} fail, ` +
    `${report.scopes.setup.summary.warn} warn, ${report.durationMs} ms`,
  );
}

