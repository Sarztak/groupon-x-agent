const puppeteer = require('puppeteer');
const fs = require('fs');

const STEP = 600;
const CATEGORIES = ['spa', 'restaurant', 'fitness', 'things+to+do'];
const CITIES = [
    {
        name: 'Chicago',
        location: btoa(JSON.stringify({ division: "chicago", lat: 41.8827, lng: -87.6233, friendlyName: "chicago" }))
    },
    {
        name: 'New York',
        location: btoa(JSON.stringify({ division: "new-york", lat: 40.6943, lng: -73.9249, friendlyName: "new york" }))
    },
    {
        name: 'Los Angeles',
        location: btoa(JSON.stringify({ division: "los-angeles", lat: 34.0194, lng: -118.4108, friendlyName: "los angeles" }))
    }
];

async function waitForSettle(page, timeout = 2000) {
    await page.waitForFunction(
        () => document.readyState === 'complete',
        { timeout }
    ).catch(() => {});
    await new Promise(r => setTimeout(r, 500));
}

async function getDealLinks(page, category, city, totalLinks=5) {
    const url = `https://www.groupon.com/search?query=${encodeURIComponent(category)}&detectedLocation=${city.location}`;
    console.log(`  Fetching links: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await waitForSettle(page);

    let current = 0;
    const links = new Set();

    while (true) {
        const totalHeight = await page.evaluate(() => document.documentElement.scrollHeight);
        if (current >= totalHeight) break;
        await page.evaluate(y => window.scrollTo(0, y), current);
        current += STEP;
        await waitForSettle(page);

        const newLinks = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('[data-item-type="card"]'))
                .map(c => c.querySelector('a[href]')?.href)
                .filter(Boolean);
        });
        newLinks.forEach(l => links.add(l));
        if (links.size >= totalLinks) break;
    }

    return [...links];
}

async function scrapeDeal(page, url) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    await page.waitForSelector('[data-testid="featured-deal-content"]', { timeout: 10000 });
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

async function run() {
    const browser = await puppeteer.launch({ headless: false, defaultViewport: null });
    const page = await browser.newPage();
    const allDeals = [];

    for (const city of CITIES) {
        console.log(`\n📍 ${city.name}`);
        for (const category of CATEGORIES) {
            console.log(`  🔍 ${category}`);
            const links = await getDealLinks(page, category, city);
            console.log(`  Found ${links.length} links`);

            for (const url of links) {
                const truncatedURL = url.split('?redemptionLocationId')[0];
                const newBrowser = await puppeteer.launch({ headless: false, defaultViewport: null });
                const newPage = await newBrowser.newPage();
                try {
                    console.log(`    Scraping: ${url}`);
                    const deal = await scrapeDeal(newPage, truncatedURL);
                    if (deal && deal.deal_title) {
                        allDeals.push({
                            ...deal,
                            category,
                            city: city.name,
                            url
                        });
                        console.log(`    ✓ ${deal.deal_title}`);
                    }
                    await new Promise(r => setTimeout(r, 1500));
                } catch (e) {
                    console.log(`    ✗ Failed: ${e.message}`);
                } finally {
                    await newBrowser.close();
                }
            }
        }
    }

    fs.writeFileSync('deals_catalog.json', JSON.stringify(allDeals, null, 2));
    console.log(`\n✅ Saved ${allDeals.length} deals to deals_catalog.json`);
    await browser.close();
}

run().catch(console.error);
