import { build } from 'astro';
import fs from 'fs-extra';
import path from 'path';

process.on('uncaughtException', (err) => {
  console.error('--- BUILD SYSTEM UNCAUGHT EXCEPTION ---');
  console.error(err);
});
process.on('unhandledRejection', (reason) => {
  console.error('--- BUILD SYSTEM UNHANDLED REJECTION ---');
  console.error(reason);
});

const pathPageFile = path.resolve('src/pages/keystatic/[...params].astro');
let pageFileBackup = null;
const pathApi = path.resolve('src/pages/api/keystatic');
const pathApiTemp = path.resolve('temp-keystatic-api');

async function run() {
  console.log('--- Preparing build (disabling dev-only routes) ---');
  if (await fs.pathExists(pathPageFile)) {
    pageFileBackup = await fs.readFile(pathPageFile, 'utf8');
    const productionContent = `---
import { KeystaticApp } from '../../components/KeystaticApp.tsx';

export const prerender = true;

export function getStaticPaths() {
  return [
    { params: { params: undefined } },
  ];
}
---
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>莊主後台 | 唐門山莊</title>
  <script is:inline>
    (function() {
      var params = new URLSearchParams(window.location.search);
      var redirectUrl = params.get('redirect');
      if (redirectUrl) {
        window.history.replaceState(null, '', redirectUrl);
      }
    })();
  </script>
</head>
<body>
  <KeystaticApp client:only="react" />
</body>
</html>
`;
    await fs.writeFile(pathPageFile, productionContent, 'utf8');
    console.log('Configured keystatic page for static pre-rendering');
  }
  if (await fs.pathExists(pathApi)) {
    await fs.move(pathApi, pathApiTemp, { overwrite: true });
    console.log('Disabled keystatic API folder');
  }

  let buildError = null;
  try {
    console.log('--- Running Astro Build (Programmatic) ---');
    // 強制注入 build 參數，確保 config 判定為生產建置
    if (!process.argv.includes('build')) {
      process.argv.push('build');
    }
    await build({});
  } catch (err) {
    buildError = err;
  } finally {
    console.log('--- Cleaning up (restoring dev-only routes) ---');
    if (pageFileBackup !== null) {
      await fs.writeFile(pathPageFile, pageFileBackup, 'utf8');
      console.log('Restored keystatic page file content');
    }
    if (await fs.pathExists(pathApiTemp)) {
      await fs.move(pathApiTemp, pathApi, { overwrite: true });
      console.log('Restored keystatic API folder');
    }
  }

  if (buildError) {
    console.error('Build failed with error:');
    console.error(buildError);
    process.exit(1);
  } else {
    console.log('Build completed successfully!');
  }
}
run();
