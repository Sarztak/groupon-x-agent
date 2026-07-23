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

async function getDealLinks(page, category, city) {
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
        if (links.size >= 15) break;
    }

    return [...links];
}

async function scrapeDeal(page, url) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await waitForSettle(page);

    return page.evaluate(() => {
        const content = document.querySelector('[data-testid="featured-deal-content"]');
        if (!content) return null;

        const titles = Array.from(content.querySelectorAll('[title]'))
            .map(a => a.title).filter(t => t);

        const fullContent = content.querySelector('[data-content-type="html"]')?.innerText
                         || content.querySelector('[data-bhw="DealWriteUp"]')?.innerText
                         || null;

        return {
            deal_title:    titles[0] || null,
            merchant_name: titles[1] || null,
            location:      titles[2] || null,
            merchant_info: content.querySelector('[id="merchant"]')?.innerText || null,
            highlights:    content.querySelector('[data-bhw="HighlightsSection"]')?.innerText || null,
            full_content:  fullContent,
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
                    newBrowser.close();
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
                }
            }
        }
    }

    fs.writeFileSync('deals_catalog.json', JSON.stringify(allDeals, null, 2));
    console.log(`\n✅ Saved ${allDeals.length} deals to deals_catalog.json`);
    await browser.close();
}

run().catch(console.error);
