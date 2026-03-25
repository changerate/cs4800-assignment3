from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.services.text_snippet import word_safe_teaser

OPENALEX_WORKS_ENDPOINT = "https://api.openalex.org/works"
SOURCE_PROVIDER = "openalex"


class OpenAlexError(Exception):
    """Raised when the OpenAlex API returns an error or unexpected payload."""


@dataclass
class OpenAlexSearchParams:
    q: str | None = None
    title: str | None = None
    author: str | None = None
    concept_id: str | None = None
    year: int | None = None
    is_oa: bool | None = None
    sort: str = "recency"
    per_page: int = 25
    cursor: str | None = None


def discovery_has_criteria(params: OpenAlexSearchParams) -> bool:
    """Require at least one filter or search term (cursor alone is allowed for paging)."""
    if params.cursor:
        return True
    if (params.q or "").strip():
        return True
    if (params.title or "").strip():
        return True
    if (params.author or "").strip():
        return True
    if (params.concept_id or "").strip():
        return True
    if params.year is not None:
        return True
    if params.is_oa is not None:
        return True
    return False


def openalex_record_id(work_id_url: str | None) -> str | None:
    if not work_id_url:
        return None
    return work_id_url.rstrip("/").rsplit("/", 1)[-1]


def normalize_concept_filter_value(concept: str) -> str | None:
    raw = (concept or "").strip()
    if not raw:
        return None
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if raw.upper().startswith("C") and raw[1:].isdigit():
        return f"https://openalex.org/{raw.upper()}"
    if raw.isdigit():
        return f"https://openalex.org/C{raw}"
    return raw


def normalize_doi(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if s.lower().startswith(prefix.lower()):
            s = s[len(prefix) :].lstrip("/")
            break
    return s[:255] if s else None


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    slots: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            slots.append((pos, word))
    slots.sort(key=lambda item: item[0])
    return " ".join(word for _, word in slots)


def abstract_text_from_work(work: dict[str, Any]) -> str:
    inv = work.get("abstract_inverted_index")
    if inv:
        return reconstruct_abstract(inv)
    ab = work.get("abstract")
    if isinstance(ab, str) and ab.strip():
        return ab.strip()
    return ""


def _bool_query(raw: str | None) -> bool | None:
    if raw is None:
        return None
    s = raw.strip().lower()
    if s in {"", "any"}:
        return None
    if s in {"1", "true", "yes", "y"}:
        return True
    if s in {"0", "false", "no", "n"}:
        return False
    return None


def _active_search_text(params: OpenAlexSearchParams) -> str | None:
    q = (params.q or "").strip()
    if q:
        return q
    title = (params.title or "").strip()
    if params.sort == "topic_match" and title:
        return title
    return None


def build_works_request(
    params: OpenAlexSearchParams,
) -> tuple[dict[str, str], bool]:
    """Return querystring mapping and whether `search` is set (affects sorting rules)."""
    per_page = max(1, min(params.per_page, 200))
    query: dict[str, str] = {"per-page": str(per_page)}

    filters: list[str] = []
    if params.year is not None:
        filters.append(f"publication_year:{int(params.year)}")
    if params.is_oa is not None:
        filters.append(f"open_access.is_oa:{str(params.is_oa).lower()}")
    cid = normalize_concept_filter_value(params.concept_id or "")
    if cid:
        filters.append(f"concept.id:{cid}")
    author = (params.author or "").strip()
    if author:
        if " " in author:
            filters.append(f'raw_author_name.search:"{author}"')
        else:
            filters.append(f"raw_author_name.search:{author}")
    title_only = (params.title or "").strip()
    search_text = _active_search_text(params)
    if title_only and not search_text:
        if " " in title_only:
            filters.append(f'title.search:"{title_only}"')
        else:
            filters.append(f"title.search:{title_only}")
    elif title_only and search_text and search_text != title_only:
        if " " in title_only:
            filters.append(f'title.search:"{title_only}"')
        else:
            filters.append(f"title.search:{title_only}")

    if filters:
        query["filter"] = ",".join(filters)

    if search_text:
        query["search"] = search_text

    uses_relevance = False
    sort = (params.sort or "recency").strip().lower()
    if sort == "citations":
        query["sort"] = "cited_by_count:desc"
    elif sort == "topic_match" and search_text:
        query["sort"] = "relevance_score:desc"
        uses_relevance = True
    else:
        query["sort"] = "publication_date:desc"

    if params.cursor:
        query["cursor"] = params.cursor

    return query, uses_relevance


def fetch_openalex_works(
    params: OpenAlexSearchParams,
    mailto: str | None = None,
    timeout_s: float = 25.0,
) -> dict[str, Any]:
    query, _ = build_works_request(params)
    if mailto:
        query = {**query, "mailto": mailto}
    url = f"{OPENALEX_WORKS_ENDPOINT}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "CampusResearch/1.0 (OpenAlex discovery; +https://openalex.org)",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise OpenAlexError(f"OpenAlex HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise OpenAlexError(f"OpenAlex network error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise OpenAlexError("OpenAlex returned non-JSON body") from exc

    if not isinstance(payload, dict) or "results" not in payload:
        raise OpenAlexError("OpenAlex payload missing results")
    return payload


def pick_landing_pdf_urls(work: dict[str, Any]) -> tuple[str | None, str | None]:
    primary = work.get("primary_location") or {}
    best_oa = work.get("best_oa_location") or {}

    landing = primary.get("landing_page_url") or best_oa.get("landing_page_url")
    pdf_url = (
        (best_oa.get("pdf_url") if isinstance(best_oa, dict) else None)
        or primary.get("pdf_url")
    )
    if not pdf_url:
        for loc in work.get("locations") or []:
            if isinstance(loc, dict) and loc.get("pdf_url"):
                pdf_url = loc["pdf_url"]
                break
    if landing and len(landing) > 1000:
        landing = landing[:1000]
    if pdf_url and len(pdf_url) > 1000:
        pdf_url = pdf_url[:1000]
    return landing, pdf_url


def normalize_openalex_work(work: dict[str, Any]) -> dict[str, Any]:
    """Map a single OpenAlex work JSON object into ResearchPaper column kwargs."""
    title = (work.get("title") or work.get("display_name") or "").strip()
    abs_text = abstract_text_from_work(work)
    if not abs_text:
        abs_text = "No abstract is available for this work in OpenAlex."

    published_at: date | None = None
    pub_date = work.get("publication_date")
    if isinstance(pub_date, str) and pub_date.strip():
        try:
            published_at = datetime.strptime(pub_date[:10], "%Y-%m-%d").date()
        except ValueError:
            published_at = None
    if published_at is None and work.get("publication_year") is not None:
        try:
            published_at = date(int(work["publication_year"]), 1, 1)
        except (TypeError, ValueError):
            published_at = None

    primary = work.get("primary_location") or {}
    src = primary.get("source") or {}
    venue = (src.get("display_name") or "").strip()[:200]
    publisher = (src.get("host_organization_name") or "").strip()[:500]

    landing_url, pdf_url = pick_landing_pdf_urls(work)

    authors: list[dict[str, str]] = []
    for row in work.get("authorships") or []:
        if not isinstance(row, dict):
            continue
        author = row.get("author") or {}
        if not isinstance(author, dict):
            continue
        name = (author.get("display_name") or "").strip()
        if name:
            authors.append({"display_name": name})

    oa = work.get("open_access") or {}
    is_oa = oa.get("is_oa") if isinstance(oa, dict) else None
    oa_status = (oa.get("oa_status") or "").strip()[:32] if isinstance(oa, dict) else None
    oa_url = oa.get("oa_url") if isinstance(oa, dict) else None
    if isinstance(oa_url, str) and len(oa_url) > 1000:
        oa_url = oa_url[:1000]

    concepts_raw = [
        c for c in (work.get("concepts") or []) if isinstance(c, dict)
    ]
    concepts_raw.sort(
        key=lambda c: float(c.get("score") or 0.0),
        reverse=True,
    )
    topic_tags = [
        (c.get("display_name") or "").strip()
        for c in concepts_raw[:18]
        if (c.get("display_name") or "").strip()
    ]

    primary_topic = work.get("primary_topic") if isinstance(work.get("primary_topic"), dict) else {}
    topic_label = (primary_topic.get("display_name") or "").strip()
    if not topic_label and topic_tags:
        topic_label = topic_tags[0]
    if not topic_label:
        topic_label = "Uncategorized"
    topic_label = topic_label[:120]

    cited = work.get("cited_by_count")
    try:
        cited_by_count = int(cited) if cited is not None else None
    except (TypeError, ValueError):
        cited_by_count = None

    feed_summary = word_safe_teaser(abs_text, max_len=220)
    rid = openalex_record_id(work.get("id"))

    return {
        "title": title[:500] if title else "Untitled work",
        "abstract": abs_text,
        "feed_summary": feed_summary,
        "topic": topic_label,
        "venue": venue or None,
        "published_at": published_at,
        "doi": normalize_doi(work.get("doi")),
        "authors_json": json.dumps(authors) if authors else None,
        "publisher": publisher or None,
        "is_open_access": bool(is_oa) if isinstance(is_oa, bool) else None,
        "oa_status": oa_status or None,
        "oa_url": oa_url if oa_url else None,
        "landing_url": landing_url,
        "pdf_url": pdf_url,
        "topic_tags_json": json.dumps(topic_tags) if topic_tags else None,
        "cited_by_count": cited_by_count,
        "source_provider": SOURCE_PROVIDER,
        "source_record_id": rid,
    }


def discover_params_from_request_args(args: Any) -> OpenAlexSearchParams:
    """Build search params from Flask `request.args` mapping."""
    year_raw = (args.get("year") or "").strip()
    year: int | None = None
    if year_raw.isdigit():
        year = int(year_raw)

    per_page_raw = (args.get("per_page") or args.get("limit") or "25").strip()
    try:
        per_page = int(per_page_raw)
    except ValueError:
        per_page = 25

    is_oa = _bool_query(args.get("is_oa"))

    sort = (args.get("sort") or "recency").strip().lower()
    if sort not in {"recency", "citations", "topic_match"}:
        sort = "recency"

    return OpenAlexSearchParams(
        q=(args.get("q") or "").strip() or None,
        title=(args.get("title") or "").strip() or None,
        author=(args.get("author") or "").strip() or None,
        concept_id=(args.get("concept") or "").strip() or None,
        year=year,
        is_oa=is_oa,
        sort=sort,
        per_page=per_page,
        cursor=(args.get("cursor") or "").strip() or None,
    )
