const puppeteer = require("puppeteer");

const REDIRECT_PATHS = [
    "/landing/sale",
    "/local/beauty-and-spas",
    "/local/things-to-do",
    "/local/automotive",
    "/local/food-and-drink",
    "/gift",
    "/local",
    "/travel",
    "/goods",
    "https://www.groupon.com/coupons"
];

const DEFAULT_UTM_PARAMS = {
    utm_source: "x_organic",
    utm_medium: "social_bot",
    utm_campaign: "chicago_local_deals",
    utm_content: "auto_reply",
};

function validateAndEnrichDealUrl(rawUrl, utmParams = DEFAULT_UTM_PARAMS) {
    const parsed = new URL(rawUrl);

    if (!["www.groupon.com", "groupon.com"].includes(parsed.hostname)) {
        throw new Error(`Invalid domain: ${parsed.hostname}. Must be groupon.com`);
    }

    if (!parsed.pathname.startsWith("/deals/")) {
        throw new Error(`Invalid deal path: ${parsed.pathname}. Must start with /deals/`);
    }

    for (const [key, val] of Object.entries(utmParams)) {
        parsed.searchParams.append(key, val);
    }

    return parsed.toString();
}

async function verifyLiveDealStatus(url) {
    let browser;
    try {
        browser = await puppeteer.launch({ 
            headless: false,
            defaultViewport: null
        });
        
        const page = await browser.newPage();
        
        const response = await page.goto(url, { 
            waitUntil: "domcontentloaded", 
            timeout: 15000 
        });

        if (!response || response.status() !== 200) {
            console.log(`Deal URL returned status code: ${response ? response.status() : "No response"}`);
            await browser.close();
            return false;
        }

        const finalUrl = page.url();
        if (REDIRECT_PATHS.some(path => finalUrl.includes(path))) {
            console.log(`Deal is expired or redirected to fallback: ${finalUrl}`);
            await browser.close();
            return false;
        }

        await browser.close();
        return true;
    } catch (e) {
        console.log(`Network error checking deal URL: ${e.message}`);
        if (browser) await browser.close();
        return false;
    }
}

async function processDealUrl(rawUrl) {
    const validatedUrl = validateAndEnrichDealUrl(rawUrl);
    const result = await verifyLiveDealStatus(validatedUrl);
    console.log(`Result: ${result}`);
    return result;
}

const rawUrl = "https://www.groupon.com/deals/gl-mountain-creek-ski-resort-1?redemptionLocationId=e62c6efe-3203-bfdf-8e3a-0156cf44b523";
processDealUrl(rawUrl).catch(console.error);
