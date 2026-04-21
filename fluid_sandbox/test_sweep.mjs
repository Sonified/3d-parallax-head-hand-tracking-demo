// Minimal sweep with 5 configs, full stdout
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
server.listen(8765, () => console.log('server on 8765'));

const configs = [
    { NX: 32, NY: 16, NZ: 1, RHO: 1008, SCALE: 32, ON1: 10, OD1: 7, ON2: 8, OD2: 5, FORCE: 8,  TICKS: 1000, MODE:'poiseuille', INJECT_X:6, INJECT_TICKS:0, LUT_MODE:0, LUT_CURVE:'linear', UMAX:8 },
    { NX: 32, NY: 16, NZ: 1, RHO: 1008, SCALE: 32, ON1: 10, OD1: 7, ON2: 8, OD2: 5, FORCE: 16, TICKS: 1000, MODE:'poiseuille', INJECT_X:6, INJECT_TICKS:0, LUT_MODE:0, LUT_CURVE:'linear', UMAX:8 },
    { NX: 32, NY: 16, NZ: 1, RHO: 1008, SCALE: 32, ON1: 10, OD1: 7, ON2: 8, OD2: 5, FORCE: 32, TICKS: 1000, MODE:'poiseuille', INJECT_X:6, INJECT_TICKS:0, LUT_MODE:0, LUT_CURVE:'linear', UMAX:8 },
    { NX: 32, NY: 16, NZ: 1, RHO: 1008, SCALE: 32, ON1: 1, OD1: 1, ON2: 8, OD2: 5, FORCE: 8,  TICKS: 1000, MODE:'poiseuille', INJECT_X:6, INJECT_TICKS:0, LUT_MODE:0, LUT_CURVE:'linear', UMAX:8 },
    { NX: 32, NY: 16, NZ: 1, RHO: 1008, SCALE: 32, ON1: 1, OD1: 2, ON2: 8, OD2: 5, FORCE: 4,  TICKS: 1000, MODE:'poiseuille', INJECT_X:6, INJECT_TICKS:0, LUT_MODE:0, LUT_CURVE:'linear', UMAX:8 },
];

const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--enable-features=Vulkan','--enable-unsafe-webgpu','--disable-gpu-sandbox','--enable-gpu','--use-gl=angle'],
});
const page = await browser.newPage();
page.setDefaultTimeout(0);

page.on('console', msg => {
    const text = msg.text();
    if (text.startsWith('RESULT:')) console.log('GOT:', text.slice(7, 200));
    else console.log('[page]', text.substring(0, 200));
});
page.on('pageerror', err => console.error('PAGE ERR:', err.message));

const url = `http://localhost:8765/sim.html?configs=${encodeURIComponent(JSON.stringify(configs))}`;
console.log('URL length:', url.length);
await page.goto(url, { waitUntil: 'domcontentloaded' });
console.log('page loaded, waiting for Done...');

await page.waitForFunction(() => {
    const pre = document.getElementById('log');
    return pre && (pre.textContent.includes('Done.') || pre.textContent.includes('FATAL'));
}, { timeout: 60000 });

console.log('done');
await browser.close();
server.close();
