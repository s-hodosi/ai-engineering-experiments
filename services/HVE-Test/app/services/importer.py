from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup


def extract_job_details(url: str, html: str | None = None) -> dict[str, Any]:
    if html is None:
        raise ValueError("HTML content is required")

    soup = BeautifulSoup(html, "html.parser")
    title = _first_text(soup, ["meta[property='og:title']", "meta[name='twitter:title']", "title"])
    company = _extract_company(soup)
    location = _extract_location(soup)
    summary = _extract_summary(soup)

    return {
        "url": url,
        "title": title or "Untitled role",
        "company": company or "Unknown company",
        "location": location or "Unknown location",
        "summary": summary or "",
    }


def _first_text(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        tag = soup.select_one(selector)
        if tag is None:
            continue
        value = tag.get("content") or tag.get_text(" ", strip=True)
        if value:
            return value
    return None


def _extract_company(soup: BeautifulSoup) -> str | None:
    for selector in ["meta[name='company']", "meta[property='og:site_name']", "[data-company-name]"]:
        tag = soup.select_one(selector)
        if tag is None:
            continue
        value = tag.get("content") or tag.get_text(" ", strip=True)
        if value:
            return _clean_company_name(value)

    for tag in soup.find_all(["p", "li", "span", "h1", "h2", "h3"]):
        text = tag.get_text(" ", strip=True)
        if text and "at " in text.lower():
            return _clean_company_name(text)

    return None


def _clean_company_name(value: str) -> str:
    cleaned = value.strip()
    if cleaned.lower().startswith("at "):
        cleaned = cleaned[3:].strip()
    return cleaned


def _extract_location(soup: BeautifulSoup) -> str | None:
    for selector in ["meta[name='location']", "meta[property='og:location']"]:
        tag = soup.select_one(selector)
        if tag is None:
            continue
        value = tag.get("content") or tag.get_text(" ", strip=True)
        if value:
            return value

    for tag in soup.find_all(["p", "li", "span"]):
        text = tag.get_text(" ", strip=True)
        if text and any(term in text.lower() for term in ["remote", "hybrid", "onsite", "city", "state", "country"]):
            return text
    return None


def _extract_summary(soup: BeautifulSoup) -> str | None:
    meta_description = _first_text(soup, ["meta[name='description']", "meta[property='og:description']"])
    if meta_description:
        return meta_description

    text_blocks = []
    for tag in soup.find_all(["p", "li", "section"]):
        text = tag.get_text(" ", strip=True)
        if text and len(text) > 30:
            text_blocks.append(text)
    if text_blocks:
        return " ".join(text_blocks[:2])
    return None
