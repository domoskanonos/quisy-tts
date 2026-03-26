import { test } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const outDir = path.resolve(__dirname, '..', 'reports', 'axe');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

const routes = ['/', '/voices', '/synthesis'];

test.describe('Axe accessibility scans', () => {
  for (const r of routes) {
    test(`axe scan ${r}`, async ({ page }) => {
      const url = r === '/' ? '/ui/' : `/ui${r}`;
      await page.goto(url, { waitUntil: 'load' });

      // inject axe-core from CDN
      await page.addScriptTag({ url: 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.0/axe.min.js' });
      const results = await page.evaluate(async () => {
        // @ts-ignore
        return await (window as any).axe.run(document, { runOnly: { type: 'tag', values: ['wcag2aa', 'wcag21aa'] } });
      });

      const outPath = path.join(outDir, `${r === '/' ? 'home' : r.replace('/', '')}.json`);
      fs.writeFileSync(outPath, JSON.stringify(results, null, 2));
    });
  }
});
