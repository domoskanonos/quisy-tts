import { test } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const outDir = path.resolve(__dirname, '..', 'reports', 'screenshots');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

const routes = ['/', '/voices', '/synthesis'];
// Playwright baseURL is configured in playwright.config.ts (http://localhost:4200/ui)

test.describe('UI Screenshots', () => {
  for (const r of routes) {
    test(`screenshot ${r}`, async ({ page }) => {
      // ensure we navigate to the configured base path
      const pathUrl = r === '/' ? '/ui/' : `/ui${r}`;
      await page.goto(pathUrl);
      const name = r === '/' ? 'home' : r.replace('/', '');
      await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: true });
    });
  }
});
