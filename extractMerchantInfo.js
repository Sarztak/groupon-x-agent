const fs = require('fs');
const { spawnSync } = require('child_process');

const systemPrompt = fs.readFileSync('./prompts/extract_merchant_info.txt', 'utf8');
const deals = JSON.parse(fs.readFileSync('./deals_catalog.json', 'utf8'));

for (let i = 0; i < deals.length; i++) {
    const deal = deals[i];

    if (!deal.full_content) {
        deal.merchant_description = null;
        deal.key_services = null;
        console.log(`  ${i + 1}/${deals.length}: skipped (no full_content)`);
        continue;
    }

    const userMessage = `${systemPrompt}\n\n## Input\n\n${deal.full_content}`;

    const result = spawnSync('claude', ['-p', userMessage, '--model', 'claude-haiku-4-5-20251001'], {
        encoding: 'utf8',
        timeout: 60000
    });

    if (result.error || result.status !== 0) {
        console.log(`✗ ${i + 1}/${deals.length}: ${deal.merchant_name} — ${result.stderr || result.error}`);
        deal.merchant_description = null;
        deal.key_services = null;
        continue;
    }

    try {
        const raw = result.stdout.trim().replace(/^```json\n?/, '').replace(/\n?```$/, '');
        const extracted = JSON.parse(raw);
        deal.merchant_description = extracted.merchant_description ?? null;
        deal.key_services = extracted.key_services ?? null;
        console.log(`✓ ${i + 1}/${deals.length}: ${deal.merchant_name}`);
    } catch (e) {
        console.log(`✗ ${i + 1}/${deals.length}: parse failed — ${result.stdout.slice(0, 100)}`);
        deal.merchant_description = null;
        deal.key_services = null;
    }
}

fs.writeFileSync('./deals_catalog.json', JSON.stringify(deals, null, 2));
console.log('\nDone.');
