// Launch sim_batch.html, capture all RESULT lines.
import puppeteer from 'puppeteer';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const server = http.createServer((req, res) => {
    try {
        const url = req.url.split('?')[0];
        const filePath = path.join(__dirname, url === '/' ? 'sim_batch.html' : url);
        const data = fs.readFileSync(filePath);
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(data);
    } catch (e) {
        if (!res.headersSent) { res.writeHead(404); }
        res.end();
    }
});
server.listen(8766);

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const outPath = path.join(__dirname, `results_batch_${ts}.jsonl`);
const out = fs.createWriteStream(outPath);

const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--enable-features=Vulkan','--enable-unsafe-webgpu','--disable-gpu-sandbox','--enable-gpu','--use-gl=angle'],
});
const page = await browser.newPage();
page.setDefaultTimeout(0);

let count = 0;
page.on('console', msg => {
    const t = msg.text();
    if (t.startsWith('RESULT:')) {
        out.write(t.slice(7) + '\n');
        count++;
    } else if (!t.startsWith('Failed to load')) {
        console.log('[page]', t.substring(0, 200));
    }
});
page.on('pageerror', e => console.error('PAGE ERR:', e.message));

const t0 = Date.now();
await page.goto('http://localhost:8766/sim_batch.html', { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => {
    const pre = document.getElementById('log');
    return pre && (pre.textContent.includes('Done.') || pre.textContent.includes('FATAL'));
}, { timeout: 0 });

const elapsed = (Date.now() - t0) / 1000;
console.log(`\nDone. ${count} results in ${elapsed.toFixed(1)}s → ${outPath}`);

out.end();
await browser.close();
server.close();
