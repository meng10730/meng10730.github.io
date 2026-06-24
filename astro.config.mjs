// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';

import react from '@astrojs/react';
import keystatic from '@keystatic/astro';

// https://astro.build/config
export default defineConfig(({ command }) => {
  const isDev = command === 'dev';
  return {
    // GitHub 帳號：meng10730，儲存庫須命名為 meng10730.github.io（個人主頁格式）
    site: 'https://meng10730.github.io',
    base: '/',
    integrations: [
      react(),
      ...(isDev ? [keystatic()] : []),
      mdx()
    ],
    output: isDev ? 'hybrid' : 'static',
  };
});
