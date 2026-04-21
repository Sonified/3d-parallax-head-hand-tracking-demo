// Hunt for u10 Poiseuille parabola where:
//   1. FORCE >= 32 (registers at RHO=1008/SCALE=32)
//   2. u_anal naturally fits under UMAX (no clamping at center)
import puppeteer from 'puppeteer';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const server = http.createServer((req, res) => {
    const url = req.url.split('?')[0];
    const filePath = path.join(__dirname, url === '/' ? 'sim.html' : url);
    try { res.writeHead(200); res.end(fs.readFileSync(filePath)); }
    catch { res.writeHead(404); res.end(); }
});
server.listen(8765);

const base = {
    NX: 32, NZ: 1, RHO: 1008, SCALE: 32,
    ON2: 8, OD2: 5, INJECT_X: 6, INJECT_TICKS: 0,
    MODE: 'poiseuille',
    LUT_MODE: 0, LUT_CURVE: 'linear',
    UMAX: 16,  // generous clamp (Ma=0.87)
    TICKS: 3000,
};

// High viscosity: tau1 = OD1/ON1
// tau=2 → ON1=1,OD1=2 (nu=0.5)
// tau=3 → ON1=1,OD1=3 (nu=0.83)
// tau=5 → ON1=1,OD1=5 (nu=1.5)
// tau=10 → ON1=1,OD1=10 (nu=3.17)
// tau=20 → ON1=1,OD1=20 (nu=6.5)
const tauPairs = [
    [1,2,'tau=2'],[1,3,'tau=3'],[1,5,'tau=5'],[1,10,'tau=10'],[1,20,'tau=20'],[1,50,'tau=50']
];
const NYs = [4, 6, 8, 12];
const forces = [32, 64, 96, 128];

const configs = [];
for (const NY of NYs)
    for (const [ON1, OD1, label] of tauPairs)
        for (const F of forces)
            configs.push({ ...base, NY, ON1, OD1, FORCE: F, _label: label });

console.log(`Configs: ${configs.length}`);

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const outPath = path.join(__dirname, `results_hunt_${ts}.jsonl`);
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
        process.stdout.write(`\r${count}/${configs.length}`);
    }
});

const url = `http://localhost:8765/sim.html?configs=${encodeURIComponent(JSON.stringify(configs))}`;
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForFunction(() => {
    const pre = document.getElementById('log');
    return pre && (pre.textContent.includes('Done.') || pre.textContent.includes('FATAL'));
}, { timeout: 0 });

console.log(`\nWrote ${outPath}`);
out.end();
await browser.close();
server.close();
