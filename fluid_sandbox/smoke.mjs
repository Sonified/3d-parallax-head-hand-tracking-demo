// Single-config smoke test
import puppeteer from 'puppeteer';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const server = http.createServer((req, res) => {
    const url = req.url.split('?')[0];
    const filePath = path.join(__dirname, url === '/' ? 'sim.html' : url);
    try {
        const data = fs.readFileSync(filePath);
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(data);
    } catch { res.writeHead(404); res.end(); }
});
server.listen(8765);

const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--enable-features=Vulkan', '--enable-unsafe-webgpu', '--disable-gpu-sandbox', '--enable-gpu', '--use-gl=angle'],
});
const page = await browser.newPage();
page.setDefaultTimeout(0);

page.on('console', msg => { console.log('[page]', msg.text()); });
page.on('pageerror', err => console.error('PAGE ERR:', err.message));

const cfg = [{
    NX: 64, NY: 32, NZ: 4,
    RHO: 1008, SCALE: 32,
    ON1: 10, OD1: 7, ON2: 8, OD2: 5,
    FORCE: 32, TICKS: 8000,
    MODE: 'poiseuille',
    INJECT_X: 6, INJECT_TICKS: 100,
    LUT_MODE: 1, LUT_CURVE: 'tanh', UMAX: 5,
}];

await page.goto(`http://localhost:8765/sim.html?configs=${encodeURIComponent(JSON.stringify(cfg))}`, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => {
    const pre = document.getElementById('log');
    return pre && (pre.textContent.includes('Done.') || pre.textContent.includes('FATAL'));
}, { timeout: 60000 });

await browser.close();
server.close();
