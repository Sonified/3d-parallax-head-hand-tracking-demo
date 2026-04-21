// Quick standalone sweep using sweep.mjs's logic but with custom configs
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

// Carefully chosen configs to find a parabola at u10
const base = {
    NX: 32, NZ: 1, RHO: 1008, SCALE: 32,
    ON2: 8, OD2: 5,
    INJECT_X: 6, INJECT_TICKS: 0,
    MODE: 'poiseuille',
    LUT_MODE: 0, LUT_CURVE: 'linear',
};

const configs = [];
// Sweep small NY × tau × force, no LUT (raw clamp won't trigger if u_anal < UMAX)
for (const NY of [8, 16]) {
    for (const [ON1, OD1] of [[1,2],[2,3],[3,4],[10,7]]) {  // tau=0.5, 0.67, 0.75, 1.43
        for (const F of [4, 8, 16]) {
            for (const UMAX of [16]) {  // generous clamp
                configs.push({ ...base, NY, ON1, OD1, FORCE: F, UMAX, TICKS: 1500 });
            }
        }
    }
}
console.log(`Configs: ${configs.length}`);

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const outPath = path.join(__dirname, `results_tiny_${ts}.jsonl`);
const out = fs.createWriteStream(outPath);

const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--enable-features=Vulkan','--enable-unsafe-webgpu','--disable-gpu-sandbox','--enable-gpu','--use-gl=angle'],
});
const page = await browser.newPage();
page.setDefaultTimeout(0);

let count = 0;
page.on('console', msg => {
    const text = msg.text();
    if (text.startsWith('RESULT:')) {
        out.write(text.slice(7) + '\n');
        count++;
        process.stdout.write(`\r${count}/${configs.length}`);
    }
});
page.on('pageerror', e => console.error('PAGE ERR:', e.message));

const url = `http://localhost:8765/sim.html?configs=${encodeURIComponent(JSON.stringify(configs))}`;
console.log('URL length:', url.length);
const t0 = Date.now();
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => {
    const pre = document.getElementById('log');
    return pre && (pre.textContent.includes('Done.') || pre.textContent.includes('FATAL'));
}, { timeout: 0 });
const elapsed = (Date.now() - t0) / 1000;
console.log(`\nDone. ${count}/${configs.length} in ${elapsed.toFixed(0)}s`);

out.end();
await browser.close();
server.close();
