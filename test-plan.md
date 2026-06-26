# MCP Chatbot Test Plan

## Overview
CLI-based end-to-end testing of the MCP chatbot. Run in GUI terminal, capture screenshots, produce evidence.md.

## Pre-Test Setup
1. Clean existing scraped data (rename scraped_content/ and test.db to backup) for fresh test
2. Ensure .env has ANTHROPIC_API_KEY and FIRECRAWL_API_KEY
3. Verify `uv sync` succeeds

## Test Cases

### Test 1: Server Initialization
**Action:** Run `source .env && uv run starter_client.py`
**Pass criteria:**
- All 3 MCP servers initialize (llm_inference, sqlite, filesystem)
- Output shows "Connected to 3 server(s)"
- Available tools list is printed (should include scrape_websites, extract_scraped_info, read_query, write_query, etc.)
- "Data extraction enabled" message appears
- `Query:` prompt appears
**Fail criteria:** Any server fails to initialize, missing tools, or crash before prompt

### Test 2: Scrape + Query - CloudRift AI (Prompt 1)
**Action:** Type: `How much does cloudrift ai (https://www.cloudrift.ai/inference) charge for deepseek v3?`
**Pass criteria:**
- Claude calls `scrape_websites` tool with cloudrift URL
- Scraping completes without error
- Claude provides a response about pricing (may note DeepSeek V3 not available)
- Data is extracted and stored in SQLite
- scraped_content/ directory has cloudrift files + scraped_metadata.json
**Fail criteria:** `scrape_url` or `scrape` API error, crash, infinite loop, no response

### Test 3: Scrape + Query - DeepInfra (Prompt 2)
**Action:** Type: `How much does deepinfra (https://deepinfra.com/pricing) charge for deepseek v3`
**Pass criteria:**
- Claude calls `scrape_websites` tool with deepinfra URL
- Scraping completes without error
- Claude provides specific pricing for DeepSeek V3 (input/output token costs)
- Data is extracted and stored in SQLite
- scraped_content/ directory has deepinfra files
**Fail criteria:** Scraping error, no pricing data found, crash

### Test 4: Comparison Query (Prompt 3)
**Action:** Type: `Compare cloudrift ai and deepinfra's costs for deepseek v3`
**Pass criteria:**
- Claude uses cached scraped data (does NOT re-scrape)
- Claude produces a comparison of the two providers
- Response references both providers' pricing
**Fail criteria:** Re-scrapes unnecessarily, infinite loop, no comparison produced

### Test 5: Show Stored Data
**Action:** Type: `show data`
**Pass criteria:**
- Displays pricing records from SQLite
- Records include company_name, plan_name, input_tokens, output_tokens
- Multiple records visible (from both CloudRift and DeepInfra queries)
**Fail criteria:** Error querying database, no records, empty output

### Test 6: Clean Exit
**Action:** Type: `quit`
**Pass criteria:** Chatbot exits cleanly without errors
**Fail criteria:** Crash or hang on exit

## Known Risk
The merged `starter_server.py` uses `app.scrape_url(url, params={'formats': formats})` and `result.get(fmt, "")`. In firecrawl v4.30.3, `scrape_url` exists but may not work correctly with the `params` kwarg, and the return type may be a Document object (not dict). If Tests 2/3 fail due to this, I will exit test mode, fix the server code, push a new PR, and re-test.

## Evidence Collection
- Screenshot after each test step showing terminal output
- Final evidence.md with all screenshots and pass/fail results
