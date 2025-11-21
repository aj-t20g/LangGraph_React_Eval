import os
import re
from typing import Optional, Union, List
from langchain_core.tools import tool
from tavily import TavilyClient


def format_search_results_for_agent(tavily_result):
    """Format Tavily search results for the agent."""
    if not tavily_result or "results" not in tavily_result or not tavily_result["results"]:
        return "No search results found."

    formatted_results = []
    for i, doc in enumerate(tavily_result["results"], 1):
        title = doc.get("title", "No title")
        url = doc.get("url", "No URL")
        formatted_doc = f"\nRESULT {i}:\nTitle: {title}\nURL: {url}\n"

        raw_content = doc.get("raw_content")
        if raw_content and raw_content.strip():
            formatted_doc += f"Raw Content: {raw_content.strip()}\n"
        else:
            content = doc.get("content", "").strip()
            formatted_doc += f"Content: {content}\n"

        formatted_results.append(formatted_doc)

    return "\n" + "\n".join(formatted_results)


@tool
def web_search(query: str, time_range: Optional[str] = None, include_domains: Optional[str] = None) -> str:
    """Perform a web search. Returns the search results as a string, with the title, url, and content of each result ranked by relevance.

    Args:
        query: The search query to be sent for the web search.
        time_range: Limits results to content published within a specific timeframe.
            Valid values: 'd' (day - 24h), 'w' (week - 7d), 'm' (month - 30d), 'y' (year - 365d).
            Defaults to None.
        include_domains: A list of domains to restrict search results to.
            Only results from these domains will be returned. Defaults to None.

    Returns:
        The web search results as a formatted string.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not found in environment variables."

    client = TavilyClient(api_key=api_key)
    formatted_results = format_search_results_for_agent(
        client.search(
            query=query,
            max_results=10,
            time_range=time_range,
            include_domains=include_domains,
        )
    )
    return formatted_results


def format_extract_results_for_agent(tavily_result):
    """Format Tavily extract results for the agent."""
    if not tavily_result or "results" not in tavily_result:
        return "No extract results found."

    formatted_results = []
    results = tavily_result.get("results", [])

    for i, doc in enumerate(results, 1):
        url = doc.get("url", "No URL")
        raw_content = doc.get("raw_content", "")
        images = doc.get("images", [])

        formatted_doc = f"\nEXTRACT RESULT {i}:\nURL: {url}\n"

        if raw_content:
            if len(raw_content) > 5000:
                formatted_doc += f"Content: {raw_content[:5000]}...\n"
            else:
                formatted_doc += f"Content: {raw_content}\n"
        else:
            formatted_doc += "Content: No content extracted\n"

        if images:
            formatted_doc += f"Images found: {len(images)} images\n"
            for j, image_url in enumerate(images[:3], 1):
                formatted_doc += f"  Image {j}: {image_url}\n"
            if len(images) > 3:
                formatted_doc += f"  ... and {len(images) - 3} more images\n"

        formatted_results.append(formatted_doc)

    failed_results = tavily_result.get("failed_results", [])
    if failed_results:
        formatted_results.append("\nFAILED EXTRACTIONS:\n")
        for i, failure in enumerate(failed_results, 1):
            url = failure.get("url", "Unknown URL")
            error = failure.get("error", "Unknown error")
            formatted_results.append(f"Failed {i}: {url} - {error}\n")

    response_time = tavily_result.get("response_time", 0)
    formatted_results.append(f"\nResponse time: {response_time} seconds")

    return "\n" + "".join(formatted_results)


@tool
def web_extract(urls: Union[str, List[str]], include_images: bool = False, extract_depth: str = "basic") -> str:
    """Extract content from one or more web pages using Tavily's extract API.

    Args:
        urls: A single URL string or a list of URLs to extract content from.
        include_images: Whether to also extract image URLs from the pages.
                        Defaults to False.
        extract_depth: The depth of extraction. 'basic' provides standard
                      content extraction, 'advanced' provides more detailed
                      extraction. Defaults to "basic".

    Returns:
        A formatted string containing the extracted content from each URL, including
        the full raw content, any images found (if requested), and information about
        any URLs that failed to be processed.
    """
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Error: TAVILY_API_KEY not found in environment variables."

        if isinstance(urls, str):
            urls_list = [urls]
        else:
            urls_list = urls

        cleaned_urls = []
        for url in urls_list:
            if url.strip().startswith("{") and '"url":' in url:
                m = re.search(r'"url"\s*:\s*"([^"]+)"', url)
                if m:
                    url = m.group(1)

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            cleaned_urls.append(url)

        client = TavilyClient(api_key=api_key)
        api_response = client.extract(
            urls=cleaned_urls,
            include_images=include_images,
            extract_depth=extract_depth,
        )

        formatted_results = format_extract_results_for_agent(api_response)
        return formatted_results

    except Exception as e:
        return f"Error during extraction: {e}\nURLs attempted: {urls}\nFailed to extract content."


def format_crawl_results_for_agent(tavily_result):
    """Format Tavily crawl results for the agent."""
    if not tavily_result:
        return "No crawl results found."

    formatted_results = []
    for i, doc in enumerate(tavily_result, 1):
        url = doc.get("url", "No URL")
        raw_content = doc.get("raw_content", "")

        formatted_doc = f"\nRESULT {i}:\nURL: {url}\n"

        if raw_content:
            title_line = raw_content.split("\n")[0] if raw_content else "No title"
            formatted_doc += f"Title: {title_line}\n"
            formatted_doc += (
                f"Content: {raw_content[:4000]}...\n"
                if len(raw_content) > 4000
                else f"Content: {raw_content}\n"
            )

        formatted_results.append(formatted_doc)

    return "\n" + "-" * 40 + "\n".join(formatted_results)


@tool
def web_crawl(url: str, instructions: Optional[str] = None) -> str:
    """Crawls a given URL, processes the results, and formats them into a string.

    Args:
        url: The URL of the website to crawl.
        instructions: Specific instructions to guide the
                     Tavily crawler, such as focusing on
                     certain types of content or avoiding
                     others. Defaults to None.

    Returns:
        A formatted string containing the crawl results. Each result includes
        the URL and a snippet of the page content.
        If an error occurs during the crawl process (e.g., network issue,
        API error), a string detailing the error and the attempted URL is
        returned.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not found in environment variables."

    max_depth = 2
    limit = 20

    if url.strip().startswith("{") and '"url":' in url:
        m = re.search(r'"url"\s*:\s*"([^"]+)"', url)
        if m:
            url = m.group(1)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        client = TavilyClient(api_key=api_key)
        api_response = client.crawl(
            url=url,
            max_depth=max_depth,
            limit=limit,
            instructions=instructions,
        )

        tavily_results = (
            api_response.get("results")
            if isinstance(api_response, dict)
            else api_response
        )

        formatted = format_crawl_results_for_agent(tavily_results)
        return formatted
    except Exception as e:
        return f"Error: {e}\nURL attempted: {url}\nFailed to crawl the website."


# List of all tools to be bound to the agent
research_tools = [web_search, web_extract, web_crawl]
