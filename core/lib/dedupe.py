"""Near-duplicate detection for Moltos."""

import re
from typing import List, Set, Tuple, Union

from . import schema


def normalize_text(text: str) -> str:
    """Normalize text for comparison.

    - Lowercase
    - Remove punctuation
    - Collapse whitespace
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_ngrams(text: str, n: int = 3) -> Set[str]:
    """Get character n-grams from text."""
    text = normalize_text(text)
    if len(text) < n:
        return {text}
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def get_item_text(item: schema.ItemType) -> str:
    """Get comparable text from an item."""
    if isinstance(item, schema.NewsItem):
        return item.title
    elif isinstance(item, schema.SocialItem):
        return item.text
    elif isinstance(item, schema.FinancialItem):
        return f"{item.entity_name} {item.metric_type}"
    elif isinstance(item, schema.AwardItem):
        return f"{item.winner_agency} {item.campaign_name}"
    elif isinstance(item, schema.PEActivityItem):
        return f"{item.target_name} {item.acquirer_name}"
    else:
        return str(item)


def find_duplicates(
    items: List[schema.ItemType],
    threshold: float = 0.7,
) -> List[Tuple[int, int]]:
    """Find near-duplicate pairs in items.

    Args:
        items: List of items to check
        threshold: Similarity threshold (0-1)

    Returns:
        List of (i, j) index pairs where i < j and items are similar
    """
    duplicates = []

    # Pre-compute n-grams
    ngrams = [get_ngrams(get_item_text(item)) for item in items]

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            similarity = jaccard_similarity(ngrams[i], ngrams[j])
            if similarity >= threshold:
                duplicates.append((i, j))

    return duplicates


def dedupe_items(
    items: List[schema.ItemType],
    threshold: float = 0.7,
) -> List[schema.ItemType]:
    """Remove near-duplicates, keeping highest-scored item.

    Args:
        items: List of items (should be pre-sorted by score descending)
        threshold: Similarity threshold

    Returns:
        Deduplicated items
    """
    if len(items) <= 1:
        return items

    # Find duplicate pairs
    dup_pairs = find_duplicates(items, threshold)

    # Mark indices to remove (always remove the lower-scored one)
    to_remove = set()
    for i, j in dup_pairs:
        # Keep the higher-scored one (lower index in sorted list)
        if items[i].score >= items[j].score:
            to_remove.add(j)
        else:
            to_remove.add(i)

    # Return items not marked for removal
    return [item for idx, item in enumerate(items) if idx not in to_remove]


def dedupe_by_url(items: List[schema.ItemType]) -> List[schema.ItemType]:
    """Remove exact URL duplicates, keeping highest-scored item."""
    if len(items) <= 1:
        return items

    seen_urls = {}
    result = []

    for item in items:
        url = getattr(item, "url", None) or getattr(item, "source_url", None)
        if not url:
            result.append(item)
            continue

        if url in seen_urls:
            # Keep higher scored one
            existing_idx = seen_urls[url]
            if item.score > result[existing_idx].score:
                result[existing_idx] = item
        else:
            seen_urls[url] = len(result)
            result.append(item)

    return result


def dedupe_news(items: List[schema.NewsItem], threshold: float = 0.7) -> List[schema.NewsItem]:
    """Dedupe news items."""
    # First dedupe by URL
    items = dedupe_by_url(items)
    # Then by content similarity
    return dedupe_items(items, threshold)


def dedupe_social(items: List[schema.SocialItem], threshold: float = 0.7) -> List[schema.SocialItem]:
    """Dedupe social items."""
    items = dedupe_by_url(items)
    return dedupe_items(items, threshold)
