# MCP Chatbot - End-to-End Test Evidence

**Date:** 2026-06-26  
**PR:** [#2 - fix: use correct Firecrawl v2 API for scraping](https://github.com/alexis-htc/mcp/pull/2)  
**Branch:** `devin/1782439224-fix-firecrawl-api`

---

## Test 1: Scrape 4 Websites

**Query:**
```
scrape these sites: {'cloudrift': 'https://www.cloudrift.ai/inference', 'deepinfra': 'https://deepinfra.com/pricing', 'fireworks': 'https://fireworks.ai/pricing#serverless-pricing', 'groq': 'https://groq.com/pricing'}
```

**Result: PASSED**

- All 4 websites scraped successfully (cloudrift, deepinfra, fireworks, groq)
- No "unexpected keyword argument 'params'" errors (the bug from PR #1)
- Content saved to `scraped_content/` directory (8 files: markdown + html per provider)
- All entries in `scraped_metadata.json` show `"success": "true"`

**Screenshot 1 - Scraping Output:**

![Test 1 - Scrape 4 Websites](https://app.devin.ai/attachments/fc469f2f-bc44-4484-86a8-9985ee905f4c/ss_40577822.png)

**Key log lines visible:**
- `Successfully scraped cloudrift`
- `Successfully scraped deepinfra`
- `Successfully scraped fireworks`
- `Successfully scraped groq`
- `"Perfect! I've successfully scraped all four websites"`

---

## Test 2: Compare Pricing (Cached Data)

**Query:**
```
Compare cloudrift ai and deepinfra's costs for deepseek v3
```

**Result: PASSED**

- Used cached scraped data (via `extract_scraped_info`) - no re-scraping
- Produced detailed comparison between CloudRift AI and DeepInfra
- CloudRift AI: Does not list DeepSeek V3 (only Qwen model at $0.15/$1.00 per 1M tokens)
- DeepInfra: Multiple DeepSeek V3 variants with specific pricing:
  - DeepSeek-V3: $0.32 input / $0.89 output
  - DeepSeek-V3-0324: $0.20 input / $0.77 output (best deal)
  - DeepSeek-V3.1: $0.21 input / $0.79 output
  - DeepSeek-V3.1-Terminus: $0.27 input / $0.95 output
  - DeepSeek-V3.2: $0.26 input / $0.38 output (lowest output cost)
- Stored 5 pricing plans to SQLite database

**Screenshot 2 - Comparison Output:**

![Test 2 - Compare Pricing](https://app.devin.ai/attachments/9ca96e84-4c5c-4245-9f4a-c7e7584aa0bb/ss_9dd92ef7.png)

---

## Test 3: Show Stored Data

**Query:**
```
show data
```

**Result: PASSED**

- Displayed all 5 stored pricing plans from SQLite database
- All records from DeepInfra with DeepSeek V3 variants
- Each record includes: id, company_name, plan_name, input_tokens, output_tokens, currency, billing_period, features, source_query, created_at

**Screenshot 3 - Database Output:**

![Test 3 - Show Data](https://app.devin.ai/attachments/f1fc6cc2-f8ab-42b2-8160-da056eaebe2e/ss_307562e0.png)

**Database contents (verified via Python):**

| ID | Company | Plan | Input ($/1M) | Output ($/1M) | Features |
|----|---------|------|-------------|--------------|----------|
| 1 | DeepInfra | DeepSeek-V3 | $0.32 | $0.89 | 160k context |
| 2 | DeepInfra | DeepSeek-V3-0324 | $0.20 | $0.77 | 160k context, prompt caching |
| 3 | DeepInfra | DeepSeek-V3.1 | $0.21 | $0.79 | 160k context, prompt caching |
| 4 | DeepInfra | DeepSeek-V3.1-Terminus | $0.27 | $0.95 | 160k context, prompt caching |
| 5 | DeepInfra | DeepSeek-V3.2 | $0.26 | $0.38 | 160k context, prompt caching, lowest output cost |

---

## Filesystem Verification

### scraped_content/ directory:
```
cloudrift_html.txt      (8,645 bytes)
cloudrift_markdown.txt  (1,932 bytes)
deepinfra_html.txt      (238,174 bytes)
deepinfra_markdown.txt  (38,578 bytes)
fireworks_html.txt      (41,009 bytes)
fireworks_markdown.txt  (4,471 bytes)
groq_html.txt           (49,211 bytes)
groq_markdown.txt       (8,145 bytes)
scraped_metadata.json   (2,653 bytes)
```

### scraped_metadata.json:
All 4 providers show `"success": "true"` with valid timestamps and content file references.

### test.db:
5 pricing plan records stored with complete data (company_name, plan_name, input_tokens, output_tokens, currency, billing_period, features).

---

## Summary

| Test | Description | Result |
|------|-------------|--------|
| 1 | Scrape 4 websites | PASSED |
| 2 | Compare pricing (cached data) | PASSED |
| 3 | Show stored data | PASSED |

**All 3 tests passed.** The Firecrawl v2 API fix in PR #2 resolves the `scrape_url()` / `params` bug that caused all scraping to fail in PR #1.
