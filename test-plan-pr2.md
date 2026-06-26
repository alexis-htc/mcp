# Test Plan: PR #2 - Fix Firecrawl v2 API

## What Changed
PR #2 fixes `starter_server.py` to use the correct Firecrawl v2 SDK API:
- `app.scrape_url(url, params={'formats': formats})` -> `app.scrape(url, formats=formats)`
- `result.get(fmt, "")` -> `getattr(result, fmt, None) or ""`
- `result.get("metadata", {}).get(...)` -> `getattr(getattr(result, 'metadata', None), ...)`
- Cache check: `if safe_name in metadata` -> `if safe_name in metadata and metadata[safe_name].get("success") == "true"`

## How to distinguish broken vs working
- **Broken (old code)**: ERROR logs with "unexpected keyword argument 'params'" for every site, scraped_content/ has no .txt files, scraped_metadata.json has all success="false"
- **Working (new code)**: No ERROR logs, scraped_content/ has markdown/html .txt files per provider, scraped_metadata.json has success="true" entries, SQLite has pricing rows

## Pre-conditions
- Clean state: no scraped_content/ directory, no test.db
- .env has both ANTHROPIC_API_KEY and FIRECRAWL_API_KEY
- On branch devin/1782439224-fix-firecrawl-api

## Test Execution (GUI Terminal - Konsole)

### Test 1: Scrape 4 Websites
**Action:** At `Query:` prompt, type:
```
scrape these sites: {'cloudrift': 'https://www.cloudrift.ai/inference', 'deepinfra': 'https://deepinfra.com/pricing', 'fireworks': 'https://fireworks.ai/pricing#serverless-pricing', 'groq': 'https://groq.com/pricing'}
```

**Pass criteria (ALL must be true):**
1. Terminal output contains NO "unexpected keyword argument" errors
2. Log lines show "Successfully scraped <provider>" for at least 3 of 4 sites (some may fail due to site availability)
3. Claude's response text mentions scraping results (not just errors)
4. Log line shows "Stored N pricing plans" where N >= 1

**Fail criteria:**
- Any "unexpected keyword argument 'params'" error appears -> Firecrawl API fix didn't work
- All 4 sites show "Failed to scrape" -> scrape() method call is still wrong
- "Stored 0 pricing plans" -> data extraction pipeline broken

**Post-test filesystem verification (via shell):**
- `ls scraped_content/` shows .txt files (e.g., cloudrift_markdown.txt)
- `cat scraped_content/scraped_metadata.json | python3 -m json.tool` shows entries with `"success": "true"`
- `sqlite3 test.db "SELECT COUNT(*) FROM pricing_plans"` returns > 0

### Test 2: Compare Cached Data (No Re-scrape)
**Action:** At `Query:` prompt, type:
```
Compare cloudrift ai and deepinfra's costs for deepseek v3
```

**Pass criteria:**
1. Terminal output does NOT show new "Scraping <provider>" log lines (should use cached data via extract_scraped_info, not scrape_websites)
2. Claude produces a comparison response mentioning both providers
3. Response includes specific pricing numbers (e.g., "$X per million tokens")

**Fail criteria:**
- New "Scraping" log lines appear -> Claude unnecessarily re-scraped
- Response says "no data found" or similar -> extract_scraped_info is broken
- Response only mentions one provider -> comparison logic failed

### Test 3: Show Stored Data
**Action:** At `Query:` prompt, type:
```
show data
```

**Pass criteria:**
1. Output shows a formatted table/list of pricing_plans records
2. Records include columns: company_name, plan_name, input_tokens, output_tokens
3. At least 2 different company_name values visible (from the 4 scraped sites)
4. Records have non-null pricing values (input_tokens and/or output_tokens)

**Fail criteria:**
- "Error showing data" message -> SQLite query failed
- Empty output / no records -> data extraction never stored anything
- Only 1 company visible -> extraction only worked for one site

## Evidence Collection
- Screenshot after Test 1 completes (showing terminal with scrape output)
- Screenshot after Test 2 completes (showing comparison response)
- Screenshot after Test 3 completes (showing data table)
- Shell verification of scraped_content/ and test.db after all tests
- All screenshots compiled into evidence.md
