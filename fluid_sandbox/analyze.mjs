#!/usr/bin/env node
// Read results JSONL and rank configs by interesting properties
// Usage: node analyze.mjs results_*.jsonl

import fs from 'fs';
import path from 'path';

const files = process.argv.slice(2);
if (files.length === 0) {
    // glob latest results files
    const dir = '.';
    const all = fs.readdirSync(dir).filter(f => f.startsWith('results_') && f.endsWith('.jsonl'));
    if (all.length === 0) { console.error('No results files. Specify path or run sweep.mjs first.'); process.exit(1); }
    files.push(...all.sort().slice(-3));  // last 3
}

const results = [];
for (const f of files) {
    const lines = fs.readFileSync(f, 'utf8').split('\n').filter(Boolean);
    for (const line of lines) {
        try { results.push(JSON.parse(line)); } catch {}
    }
    console.log(`Loaded ${lines.length} from ${f}`);
}

console.log(`\nTotal: ${results.length} results`);
const errors = results.filter(r => r.error);
const ok = results.filter(r => !r.error);
console.log(`Errors: ${errors.length}  OK: ${ok.length}`);

// ── Filter: stable u10, mass conserved, nonzero flow ──────────────────────
const stable = ok.filter(r =>
    r.u10ok &&
    Math.abs(r.massDrift) < 0.01 &&
    Math.abs(r.uMax) > 0.001
);
console.log(`Stable & flowing: ${stable.length}`);

if (stable.length === 0) {
    console.log('\nNo stable flowing configs. Showing best u10ok regardless of flow:');
    const u10s = ok.filter(r => r.u10ok).sort((a, b) => Math.abs(b.uMax) - Math.abs(a.uMax)).slice(0, 10);
    for (const r of u10s) {
        console.log(`  ${r.cfg._tag} F=${r.cfg.FORCE} tau=${(r.cfg.OD1/r.cfg.ON1).toFixed(2)} U=${r.cfg.UMAX} LUT=${r.cfg.LUT_MODE}/${r.cfg.LUT_CURVE} u_max=${r.uMax.toFixed(4)} parabola=${r.parabola_score?.toFixed(2) || '?'}`);
    }
    process.exit(0);
}

// ── Top by parabola_score (most parabolic shape) ──────────────────────────
console.log('\n=== TOP 15 BY PARABOLA SCORE ===');
const byParabola = stable.filter(r => r.parabola_score !== undefined && r.parabola_score > 0)
    .sort((a, b) => b.parabola_score - a.parabola_score).slice(0, 15);
for (const r of byParabola) {
    const c = r.cfg;
    console.log(`  parabola=${r.parabola_score.toFixed(2)}  u_max=${r.uMax.toFixed(4)}  NY=${c.NY} F=${c.FORCE} tau1=${(c.OD1/c.ON1).toFixed(2)} U=${c.UMAX} LUT=${c.LUT_MODE}/${c.LUT_CURVE} [${c._tag}]`);
}

// ── Top by absolute u_max (fastest flow) ──────────────────────────────────
console.log('\n=== TOP 10 BY MAX VELOCITY ===');
const byUMax = [...stable].sort((a, b) => Math.abs(b.uMax) - Math.abs(a.uMax)).slice(0, 10);
for (const r of byUMax) {
    const c = r.cfg;
    console.log(`  u_max=${r.uMax.toFixed(4)}  parabola=${(r.parabola_score||0).toFixed(2)}  NY=${c.NY} F=${c.FORCE} tau1=${(c.OD1/c.ON1).toFixed(2)} U=${c.UMAX} LUT=${c.LUT_MODE}/${c.LUT_CURVE}`);
}

// ── LUT comparison ────────────────────────────────────────────────────────
console.log('\n=== LUT MODE / CURVE STATS (mean across configs) ===');
const lutBuckets = {};
for (const r of stable) {
    const key = `mode${r.cfg.LUT_MODE}/${r.cfg.LUT_CURVE}`;
    if (!lutBuckets[key]) lutBuckets[key] = { count: 0, parabola: 0, u_max: 0, stable: 0 };
    lutBuckets[key].count++;
    lutBuckets[key].parabola += r.parabola_score || 0;
    lutBuckets[key].u_max += Math.abs(r.uMax);
    lutBuckets[key].stable++;
}
const lutSorted = Object.entries(lutBuckets).sort((a, b) => b[1].parabola/b[1].count - a[1].parabola/a[1].count);
for (const [key, s] of lutSorted) {
    console.log(`  ${key}: n=${s.count}  mean_parabola=${(s.parabola/s.count).toFixed(2)}  mean_u_max=${(s.u_max/s.count).toFixed(4)}`);
}

// ── Best overall: highest parabola score with strong velocity ─────────────
console.log('\n=== BEST OVERALL (parabola × log(u_max)) ===');
const scored = stable.map(r => ({
    r,
    score: (r.parabola_score || 0) * Math.log(1 + Math.abs(r.uMax) * 100)
})).sort((a, b) => b.score - a.score);

for (const { r, score } of scored.slice(0, 5)) {
    const c = r.cfg;
    console.log(`\nscore=${score.toFixed(2)}  parabola=${r.parabola_score?.toFixed(2)}  u_max=${r.uMax.toFixed(4)}`);
    console.log(`  cfg: NX=${c.NX} NY=${c.NY} NZ=${c.NZ} RHO=${c.RHO} SCALE=${c.SCALE}`);
    console.log(`       tau1=${(c.OD1/c.ON1).toFixed(3)} (ON1=${c.ON1} OD1=${c.OD1})  FORCE=${c.FORCE}  UMAX=${c.UMAX}`);
    console.log(`       LUT_MODE=${c.LUT_MODE}  LUT_CURVE=${c.LUT_CURVE}  TICKS=${c.TICKS}`);
    console.log(`  profile: ${r.profile.map(v => v.toFixed(3)).join(' ')}`);
}
