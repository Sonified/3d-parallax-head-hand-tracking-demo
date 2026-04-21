#!/usr/bin/env node
// Headless WebGPU sweep harness for u10 TRT fluid sandbox.
// Launches Chrome with WebGPU enabled, runs sim.html with batches of configs,
// streams RESULT lines to results.jsonl. No timeout.
//
// Usage:
//   node sweep.mjs <preset>
//   presets: stability, lut, resolution, parabola, all

import puppeteer from 'puppeteer';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Parameter generators ────────────────────────────────────────────────────
const log = (lo, hi, n) => {
    const out = [];
    const lh = Math.log(lo), ll = Math.log(hi);
    for (let i = 0; i < n; i++) out.push(Math.round(Math.exp(lh + (ll - lh) * i / (n-1))));
    return [...new Set(out)];
};
const lin = (lo, hi, n) => {
    const out = [];
    for (let i = 0; i < n; i++) out.push(Math.round(lo + (hi - lo) * i / (n-1)));
    return [...new Set(out)];
};
const pow2 = (lo, hi) => {
    const out = [];
    for (let v = lo; v <= hi; v *= 2) out.push(v);
    return out;
};
const taus = (vals) => vals.map(t => {
    // Convert tau to (ON, OD) integer ratio. tau = OD/ON.
    // Use simple fractions that give exact tau values.
    const candidates = [
        [1, 2, 0.5], [11, 20, 0.55], [3, 5, 0.6], [13, 20, 0.65],
        [7, 10, 0.7], [3, 4, 0.75], [4, 5, 0.8], [9, 10, 0.9],
        [1, 1, 1.0], [11, 10, 1.1], [13, 10, 1.3], [3, 2, 1.5], [2, 1, 2.0],
    ];
    // find closest
    let best = candidates[0], bestErr = Infinity;
    for (const c of candidates) {
        const e = Math.abs(c[2] - t);
        if (e < bestErr) { bestErr = e; best = c; }
    }
    return { ON1: best[0], OD1: best[1] };
});

// ── Sweep presets ───────────────────────────────────────────────────────────
function buildConfigs(preset) {
    const base = {
        NX: 64, NY: 32, NZ: 4,
        RHO: 1008, SCALE: 32,
        ON1: 10, OD1: 7,
        ON2: 8, OD2: 5,
        FORCE: 32, TICKS: 1500,
        MODE: 'poiseuille',
        INJECT_X: 6, INJECT_TICKS: 100,
        LUT_MODE: 1, LUT_CURVE: 'tanh', UMAX: 5,
    };

    const configs = [];

    if (preset === 'stability' || preset === 'all') {
        // Sweep FORCE × tau1 × UMAX with NO LUT (raw clamp at hard ceiling)
        // Find where things blow up vs stay stable
        const forces = log(2, 256, 8);              // 2,4,9,17,34,68,128,256
        const tauPairs = taus([0.55, 0.6, 0.7, 0.85, 1.0, 1.3]);  // 6 viscosities
        const umaxes = lin(2, 16, 5);              // 2,5,8,12,16
        for (const F of forces)
            for (const t of tauPairs)
                for (const U of umaxes)
                    configs.push({ ...base, FORCE: F, ...t, UMAX: U, LUT_MODE: 0, LUT_CURVE: 'linear', _tag: 'stability' });
    }

    if (preset === 'lut' || preset === 'all') {
        // Compare LUT modes and curves at a known-stable config
        const curves = ['linear', 'tanh', 'tanh_hard', 'soft_knee', 'cubic', 'sigmoid'];
        const modes = [0, 1, 2, 3];  // none, per-component, magnitude, both
        const forces = [16, 32, 64];
        for (const F of forces)
            for (const m of modes)
                for (const c of curves)
                    configs.push({ ...base, FORCE: F, LUT_MODE: m, LUT_CURVE: c, _tag: 'lut' });
    }

    if (preset === 'resolution' || preset === 'all') {
        // Sweep RHO × SCALE for precision tradeoffs
        const rhos = [504, 1008, 2016, 4032];      // 4 RHO levels (still u10 if /36 fits)
        const scales = pow2(16, 256);              // 16,32,64,128,256
        for (const R of rhos)
            for (const S of scales)
                configs.push({ ...base, RHO: R, SCALE: S, _tag: 'resolution' });
    }

    if (preset === 'parabola' || preset === 'all') {
        // Hunt for the parameter combo that produces a recognizable Poiseuille parabola
        // Cross product of small set of likely-good parameters
        const NYs = [8, 12, 16, 24];
        const tauPairs = taus([0.6, 0.7, 0.85, 1.0, 1.3, 2.0]);
        const forces = log(4, 128, 6);
        const umaxes = [3, 5, 8];
        const curves = ['tanh', 'soft_knee'];
        for (const NY of NYs)
            for (const t of tauPairs)
                for (const F of forces)
                    for (const U of umaxes)
                        for (const c of curves)
                            configs.push({ ...base, NY, FORCE: F, ...t, UMAX: U, LUT_CURVE: c, LUT_MODE: 1, TICKS: 3000, _tag: 'parabola' });
    }

    if (preset === 'spell' || preset === 'all') {
        // Sustained spell injection sweep
        const forces = log(8, 256, 6);
        const tauPairs = taus([0.55, 0.65, 0.75]);
        const umaxes = [4, 6, 8];
        const curves = ['tanh', 'soft_knee', 'sigmoid'];
        for (const F of forces)
            for (const t of tauPairs)
                for (const U of umaxes)
                    for (const c of curves)
                        configs.push({
                            ...base, NX: 96, NZ: 1, MODE: 'spell',
                            FORCE: F, ...t, UMAX: U, LUT_CURVE: c, LUT_MODE: 1,
                            TICKS: 200, INJECT_TICKS: 50,
                            _tag: 'spell'
                        });
    }

    return configs;
}

// ── Tiny static server ─────────────────────────────────────────────────────
function startServer(port) {
    return new Promise((resolve) => {
        const server = http.createServer((req, res) => {
            const url = req.url.split('?')[0];
            const filePath = path.join(__dirname, url === '/' ? 'sim.html' : url);
            try {
                const data = fs.readFileSync(filePath);
                const ext = path.extname(filePath);
                const ct = ext === '.html' ? 'text/html' : ext === '.js' || ext === '.mjs' ? 'application/javascript' : 'text/plain';
                res.writeHead(200, { 'Content-Type': ct });
                res.end(data);
            } catch {
                res.writeHead(404); res.end('Not found');
            }
        });
        server.listen(port, () => resolve(server));
    });
}

// ── Main ────────────────────────────────────────────────────────────────────
async function main() {
    const preset = process.argv[2] || 'parabola';
    const configs = buildConfigs(preset);

    if (configs.length === 0) {
        console.error(`Unknown preset: ${preset}. Try: stability, lut, resolution, parabola, spell, all`);
        process.exit(1);
    }

    console.log(`Preset: ${preset}`);
    console.log(`Configs: ${configs.length}`);

    const PORT = 8765;
    const server = await startServer(PORT);
    console.log(`Static server: http://localhost:${PORT}/`);

    // Output file (timestamped)
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const outPath = path.join(__dirname, `results_${preset}_${ts}.jsonl`);
    const outStream = fs.createWriteStream(outPath, { flags: 'a' });
    console.log(`Results → ${outPath}`);

    // Launch Chrome
    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--enable-features=Vulkan',
            '--enable-unsafe-webgpu',
            '--disable-gpu-sandbox',
            '--enable-gpu',
            '--use-gl=angle',
        ],
    });

    // Batch configs into chunks of 50 to avoid URL-length limits
    const BATCH_SIZE = 50;
    const batches = [];
    for (let i = 0; i < configs.length; i += BATCH_SIZE) {
        batches.push(configs.slice(i, i + BATCH_SIZE));
    }
    console.log(`Batches: ${batches.length} × ${BATCH_SIZE}`);

    let totalDone = 0;
    let totalErr = 0;
    const t0 = Date.now();

    for (let b = 0; b < batches.length; b++) {
        const batch = batches[b];
        const page = await browser.newPage();
        page.setDefaultTimeout(0);  // no timeout

        const url = `http://localhost:${PORT}/sim.html?configs=${encodeURIComponent(JSON.stringify(batch))}`;

        const batchResults = [];
        const batchPromise = new Promise((resolve) => {
            const handler = msg => {
                const text = msg.text();
                if (text.startsWith('RESULT:')) {
                    try {
                        const obj = JSON.parse(text.slice(7));
                        outStream.write(JSON.stringify(obj) + '\n');
                        batchResults.push(obj);
                        if (obj.error) totalErr++;
                        totalDone++;
                        const elapsed = ((Date.now() - t0) / 1000).toFixed(0);
                        process.stdout.write(`\r[${totalDone}/${configs.length}] ${elapsed}s err=${totalErr}  `);
                    } catch (e) { console.error('parse err', e); }
                }
            };
            page.on('console', handler);
            page.on('pageerror', err => console.error('\nPAGE ERR:', err.message));

            page.goto(url, { waitUntil: 'domcontentloaded' }).then(() => {
                // Wait for "Done." in the log
                page.waitForFunction(
                    () => {
                        const pre = document.getElementById('log');
                        return pre && (pre.textContent.includes('Done.') || pre.textContent.includes('FATAL'));
                    },
                    { timeout: 0 }
                ).then(resolve).catch(resolve);
            });
        });

        await batchPromise;
        await page.close();
    }

    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    console.log(`\nDone. ${totalDone} configs in ${elapsed}s. ${totalErr} errors.`);
    console.log(`Output: ${outPath}`);

    await browser.close();
    server.close();
    outStream.end();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
