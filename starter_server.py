
import os
import json
import logging
from typing import List, Dict, Optional
from firecrawl import FirecrawlApp
from urllib.parse import urlparse
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCRAPE_DIR = "scraped_content"

mcp = FastMCP("llm_inference")

@mcp.tool()
def scrape_websites(
    websites: Dict[str, str],
    formats: List[str] = ['markdown', 'html'],
    api_key: Optional[str] = None
) -> List[str]:
    """
    Scrape multiple websites using Firecrawl and store their content.
    
    Args:
        websites: Dictionary of provider_name -> URL mappings
        formats: List of formats to scrape ['markdown', 'html'] (default: both)
        api_key: Firecrawl API key (if None, expects environment variable)
        
    Returns:
        List of provider names for successfully scraped websites
    """
    
    if api_key is None:
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            raise ValueError("API key must be provided or set as FIRECRAWL_API_KEY environment variable")
    
    app = FirecrawlApp(api_key=api_key)
    
    path = os.path.join(SCRAPE_DIR)
    os.makedirs(path, exist_ok=True)
    
    # save the scraped content to files and then create scraped_metadata.json as a summary file
    # check if the provider has already been scraped and decide if you want to overwrite
    # {
    #     "cloudrift_ai": {
    #         "provider_name": "cloudrift_ai",
    #         "url": "https://www.cloudrift.ai/inference",
    #         "domain": "www.cloudrift.ai",
    #         "scraped_at": "2025-10-23T00:44:59.902569",
    #         "formats": [
    #             "markdown",
    #             "html"
    #         ],
    #         "success": "true",
    #         "content_files": {
    #             "markdown": "cloudrift_ai_markdown.txt",
    #             "html": "cloudrift_ai_html.txt"
    #         },
    #         "title": "AI Inference",
    #         "description": "Scraped content goes here"
    #     }
    # }
    metadata_file = os.path.join(path, "scraped_metadata.json")

    # Load existing metadata if present
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    scraped_providers = []

    for provider_name, url in websites.items():
        safe_name = provider_name.replace(" ", "_").replace(".", "_").lower()
        domain = urlparse(url).netloc

        # Skip if already scraped
        if safe_name in metadata:
            logger.info(f"Provider '{safe_name}' already scraped, skipping. Delete entry to re-scrape.")
            scraped_providers.append(safe_name)
            continue

        logger.info(f"Scraping {provider_name} at {url}...")
        try:
            result = app.scrape_url(url, params={'formats': formats})

            content_files = {}
            for fmt in formats:
                content = result.get(fmt, "")
                if content:
                    filename = f"{safe_name}_{fmt}.txt"
                    filepath = os.path.join(path, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    content_files[fmt] = filename

            metadata[safe_name] = {
                "provider_name": safe_name,
                "url": url,
                "domain": domain,
                "scraped_at": datetime.now().isoformat(),
                "formats": formats,
                "success": "true",
                "content_files": content_files,
                "title": result.get("metadata", {}).get("title", ""),
                "description": result.get("metadata", {}).get("description", ""),
            }

            scraped_providers.append(safe_name)
            logger.info(f"Successfully scraped {provider_name}")
        except Exception as e:
            logger.error(f"Failed to scrape {provider_name}: {e}")
            metadata[safe_name] = {
                "provider_name": safe_name,
                "url": url,
                "domain": domain,
                "scraped_at": datetime.now().isoformat(),
                "formats": formats,
                "success": "false",
                "content_files": {},
                "title": "",
                "description": str(e),
            }

    # Save updated metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)

    return scraped_providers

@mcp.tool()
def extract_scraped_info(identifier: str) -> str:
    """
    Extract information about a scraped website.
    
    Args:
        identifier: The provider name, full URL, or domain to look for
        
    Returns:
        Formatted JSON string with the scraped information
    """
    
    logger.info(f"Extracting information for identifier: {identifier}")
    logger.info(f"Files in {SCRAPE_DIR}: {os.listdir(SCRAPE_DIR)}")

    metadata_file = os.path.join(SCRAPE_DIR, "scraped_metadata.json")
    logger.info(f"Checking metadata file: {metadata_file}")

    if not os.path.exists(metadata_file):
        return json.dumps({"error": "No scraped data found. Run scrape_websites first."})

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    # Search by provider name, URL, or domain
    identifier_lower = identifier.lower().replace(" ", "_").replace(".", "_")
    match = None

    for key, entry in metadata.items():
        if (identifier_lower == key.lower()
                or identifier_lower in entry.get("url", "").lower()
                or identifier_lower in entry.get("domain", "").lower()
                or identifier.lower() in entry.get("url", "").lower()
                or identifier.lower() in entry.get("domain", "").lower()
                or identifier.lower() in key.lower()):
            match = entry
            break

    if not match:
        return json.dumps({"error": f"No data found for identifier: {identifier}",
                           "available_providers": list(metadata.keys())})

    # Read the scraped content files
    result = dict(match)
    content = {}
    for fmt, filename in match.get("content_files", {}).items():
        filepath = os.path.join(SCRAPE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content[fmt] = f.read()
    result["content"] = content

    return json.dumps(result, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")