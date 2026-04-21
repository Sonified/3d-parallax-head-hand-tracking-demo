#!/usr/bin/env node
// Run GPU benchmarks via Puppeteer, capturing console output.
// Usage: npx puppeteer node prototypes/run-bench.mjs [url]

import puppeteer from 'puppeteer';

// Default to packed-lbm-bench.html served locally. Pass a URL arg to override.
// Needs a local server: npx http-server . -p 8765 (or use batch_run.mjs's server)
const url = process.argv[2] || 'http://localhost:8765/packed-lbm-bench.html';
const TIMEOUT = 600_000; // 10 minutes max

const browser = await puppeteer.launch({
    headless: 'new',
    args: [
        '--enable-features=Vulkan',
        '--enable-unsafe-webgpu',
        '--disable-gpu-sandbox',
        '--enable-gpu',
    ]
});

const page = await browser.newPage();

const results = [];

page.on('console', msg => {
    const text = msg.text();
    if (text.startsWith('RESULT:')) {
        const json = text.slice(7);
        results.push(json);
        console.log('RESULT:' + json);
    }
});

page.on('pageerror', err => {
    console.error('PAGE ERROR:', err.message);
});

try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Wait for the "Done." text in the page or timeout
    await page.waitForFunction(
        () => {
            const pre = document.getElementById('log');
            return pre && (pre.textContent.includes('Done.') || pre.textContent.includes('FATAL'));
        },
        { timeout: TIMEOUT }
    );

    // Get the final DOM text for visual output
    const logText = await page.$eval('#log', el => el.textContent);
    console.log('\n--- DOM Output ---');
    console.log(logText);
} catch (e) {
    console.error('Timeout or error:', e.message);
    // Dump whatever we have
    try {
        const logText = await page.$eval('#log', el => el.textContent);
        console.log('\n--- Partial DOM Output ---');
        console.log(logText);
    } catch (e2) {}
}

await browser.close();
