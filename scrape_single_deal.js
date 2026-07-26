const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const { spawnSync } = require('child_process');
const fs = require('fs');

puppeteer.use(StealthPlugin());

const systemPrompt = fs.readFileSync('./prompts/extract_merchant_info.txt', 'utf8');

async function waitForSettle(page, timeout = 2000) {
    await page.waitForFunction(
        () => document.readyState === 'complete',
        { timeout }
    ).catch(() => {});
    await new Promise(r => setTimeout(r, 500));
}

async function scrapeDeal(page, url) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    await page.waitForSelector('[data-testid="featured-deal-content"]', { timeout: 15000 });
    await page.waitForFunction(
        () => !document.querySelector('[data-testid="featured-deal-content"] .animate-pulse'),
        { timeout: 15000 }
    );
    await page.waitForFunction(
        () => document.querySelector('[data-testid="deal-title"]') !== null,
        { timeout: 15000 }
    );
    await waitForSettle(page);

    return page.evaluate(() => {
        const deal = document.querySelector('[data-testid="featured-deal"]');
        if (!deal) return null;

        const merchantEl = document.querySelector('#merchant');
        let merchant_name = null;
        let merchant_info = null;
        let company_website = null;

        if (merchantEl) {
            const lines = merchantEl.innerText.split('\n').map(l => l.trim()).filter(Boolean);
            if (lines[0]?.startsWith('About ')) {
                merchant_name = lines[0].replace('About ', '');
            }
            const content = lines.slice(1).filter(l => l !== 'Company Website').join('\n');
            merchant_info = content || null;
            company_website = merchantEl.querySelector('a[href]')?.href || null;
        }

        return {
            deal_title:    document.querySelector('[data-testid="deal-title"]')?.innerText || null,
            merchant_name,
            location:      document.querySelector('[data-testid="dealLocationsList"]')?.innerText || null,
            merchant_info,
            company_website,
            highlights:    deal.querySelector('[data-bhw="HighlightsSection"]')?.innerText || null,
            full_content:  deal.querySelector('[data-bhw="DealWriteUp"]')?.innerText || null,
            reviews:       Array.from(document.querySelectorAll('[data-testid="customer-review"]'))
                               .map(c => c.innerText)
        };
    });
}

function extractInfo(full_content) {
    if (!full_content) return { merchant_description: null, key_services: null };

    const userMessage = `${systemPrompt}\n\n## Input\n\n${full_content}`;
    const result = spawnSync('claude', ['-p', userMessage, '--model', 'claude-haiku-4-5-20251001'], {
        encoding: 'utf8',
        timeout: 60000
    });

    if (result.error || result.status !== 0) {
        process.stderr.write(`Extraction failed: ${result.stderr || result.error}\n`);
        return { merchant_description: null, key_services: null };
    }

    try {
        const raw = result.stdout.trim().replace(/^```json\n?/, '').replace(/\n?```$/, '');
        return JSON.parse(raw);
    } catch (e) {
        process.stderr.write(`Extraction parse failed: ${result.stdout.slice(0, 100)}\n`);
        return { merchant_description: null, key_services: null };
    }
}

async function run() {
    const rawUrl = process.argv[2];
    if (!rawUrl) {
        process.stderr.write('Usage: node scrape_single_deal.js <groupon-deal-url>\n');
        process.exit(1);
    }

    // strip redemption param for scraping, keep full url for catalog
    const scrapeUrl = rawUrl.split('?redemptionLocationId')[0];

    const browser = await puppeteer.launch({ headless: true, defaultViewport: null });
    const page = await browser.newPage();

    try {
        process.stderr.write(`Scraping: ${scrapeUrl}\n`);
        const deal = await scrapeDeal(page, scrapeUrl);

        if (!deal || !deal.deal_title) {
            process.stderr.write('Scrape failed: no deal content found\n');
            process.exit(2);
        }

        process.stderr.write(`Scraped: ${deal.deal_title}\n`);
        process.stderr.write('Extracting merchant info...\n');

        const extracted = extractInfo(deal.full_content);

        const output = {
            ...deal,
            ...extracted,
            url: rawUrl,
            category: 'custom',
            city: null,
        };

        process.stdout.write(JSON.stringify(output));
    } catch (e) {
        process.stderr.write(`Error: ${e.message}\n`);
        process.exit(3);
    } finally {
        await browser.close();
    }
}

run().catch(e => {
    process.stderr.write(`Fatal: ${e.message}\n`);
    process.exit(4);
});
