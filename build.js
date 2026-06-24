import { execSync } from 'child_process';
import fs from 'fs-extra';
import path from 'path';

const filePage = path.resolve('src/pages/keystatic/[...params].astro');
const filePageDisabled = filePage + '.disabled';
const fileApi = path.resolve('src/pages/api/keystatic/[...params].ts');
const fileApiDisabled = fileApi + '.disabled';

async function run() {
  console.log('--- Preparing build (disabling dev-only routes) ---');
  if (await fs.pathExists(filePage)) {
    await fs.move(filePage, filePageDisabled, { overwrite: true });
    console.log('Disabled keystatic page');
  }
  if (await fs.pathExists(fileApi)) {
    await fs.move(fileApi, fileApiDisabled, { overwrite: true });
    console.log('Disabled keystatic API route');
  }

  let buildError = null;
  try {
    console.log('--- Running Astro Build ---');
    const args = process.argv.slice(2).join(' ');
    execSync(`npx astro build ${args}`, { stdio: 'inherit' });
  } catch (err) {
    buildError = err;
  } finally {
    console.log('--- Cleaning up (restoring dev-only routes) ---');
    if (await fs.pathExists(filePageDisabled)) {
      await fs.move(filePageDisabled, filePage, { overwrite: true });
      console.log('Restored keystatic page');
    }
    if (await fs.pathExists(fileApiDisabled)) {
      await fs.move(fileApiDisabled, fileApi, { overwrite: true });
      console.log('Restored keystatic API route');
    }
  }

  if (buildError) {
    console.error('Build failed!');
    process.exit(1);
  } else {
    console.log('Build completed successfully!');
  }
}
run();
