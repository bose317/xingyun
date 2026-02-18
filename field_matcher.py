"""CIP-based field-of-study matcher.

Searches the full CIP_CODES universe (2119 six-digit codes from the
official Statistics Canada CIP 2021 CSV), then resolves each hit to
the closest FIELD_OPTIONS entry for StatCan queries.

Three-tier matching:
  Tier 1 — CIP code prefix (e.g. "11", "14.08", "14.0801")
  Tier 2 — Case-insensitive keyword substring
  Tier 3 — Fuzzy ratio via SequenceMatcher
"""

import re
from difflib import SequenceMatcher

from cip_codes import CIP_CODES, CIP_TO_BROAD

MAX_RESULTS = 8


def resolve_subfield(
    cip_code: str, broad_field: str, field_options: dict
) -> tuple[str | None, str]:
    """Map a 6-digit CIP code to the nearest FIELD_OPTIONS subfield key.

    Returns (subfield_key, resolved_broad_field).

    Lookup chain (first match wins):
      1. Exact 6-digit match   (key starts with "XX.XXXX ")    — unlikely but checked
      2. 4-digit parent match  (key starts with "XX.YY ")      — e.g. "11.07" → "11.07 Computer science"
      3. 2-digit prefix match  (key starts with "XX. ")         — e.g. "11." → "11. Computer and information sciences"
    Each step is tried first in the primary broad_field, then cross-field.
    """
    # Derive the 4-digit parent: "14.0801" → "14.08"
    parent_4 = cip_code[:5]  # "XX.YY"
    prefix_2 = cip_code[:2] + "."

    def _search(info: dict) -> tuple[str | None, str | None]:
        subfields = info.get("subfields", {})
        # exact 6-digit
        for key in subfields:
            if key.startswith(cip_code + " ") or key == cip_code:
                return key, "exact6"
        # 4-digit parent
        for key in subfields:
            if key.startswith(parent_4 + " ") or key == parent_4:
                return key, "exact4"
        # 2-digit prefix (XX. level, e.g. "11. Computer and ...")
        for key in subfields:
            if key.startswith(prefix_2) and re.match(r"^\d{2}\.\s", key):
                return key, "prefix2"
        return None, None

    # Pass 1: primary broad_field
    info = field_options.get(broad_field)
    if info:
        sub, _ = _search(info)
        if sub:
            return sub, broad_field

    # Pass 2: cross-field exact (6-digit or 4-digit)
    for other_broad, other_info in field_options.items():
        if other_broad == broad_field:
            continue
        sub, kind = _search(other_info)
        if sub and kind in ("exact6", "exact4"):
            return sub, other_broad

    # Pass 3: cross-field prefix-2
    for other_broad, other_info in field_options.items():
        if other_broad == broad_field:
            continue
        sub, kind = _search(other_info)
        if sub and kind == "prefix2":
            return sub, other_broad

    return None, broad_field


def _build_candidates(field_options: dict) -> list[dict]:
    """Build searchable candidates from CIP_CODES + FIELD_OPTIONS."""
    candidates = []

    for cip_code, cip_name in CIP_CODES.items():
        prefix_2 = cip_code[:2]
        default_broad = CIP_TO_BROAD.get(prefix_2)
        if not default_broad:
            continue

        subfield, resolved_broad = resolve_subfield(
            cip_code, default_broad, field_options
        )

        candidates.append({
            "cip_code": cip_code,
            "cip_name": cip_name,
            "broad_field": resolved_broad,
            "subfield": subfield,
            "display_name": f"[CIP {cip_code}] {cip_name} \u2014 {resolved_broad}",
        })

    # Broad-field entries (no CIP code)
    for broad_name in field_options:
        candidates.append({
            "cip_code": None,
            "cip_name": None,
            "broad_field": broad_name,
            "subfield": None,
            "display_name": broad_name,
        })

    return candidates


def match_fields(query: str, field_options: dict) -> list[dict]:
    """Return up to MAX_RESULTS matches sorted by score (1.0 = best).

    Each result dict:
      - cip_code:     "11.0701" or None
      - cip_name:     "Computer science" or None
      - broad_field:  FIELD_OPTIONS key
      - subfield:     FIELD_OPTIONS subfield key or None
      - display_name: "[CIP 11.0701] Computer science — Mathematics, ..."
      - score:        float
      - match_type:   "cip" | "keyword" | "fuzzy"
    """
    query = query.strip()
    if not query:
        return []

    candidates = _build_candidates(field_options)
    query_lower = query.lower()
    # Matches patterns like "11", "14.08", "14.0801"
    is_cip = bool(re.match(r"^\d{1,2}\.?\d{0,4}$", query))

    scored: list[dict] = []

    for cand in candidates:
        cip_code = cand["cip_code"]
        cip_name = (cand["cip_name"] or "").lower()
        broad_lower = cand["broad_field"].lower()

        if cip_code:
            # Tier 1: CIP code prefix
            if is_cip:
                # Normalise query for prefix matching
                q = query_lower if "." in query_lower else query_lower.rstrip("0").rstrip(".")
                if not cip_code.startswith(q):
                    # Also try without dot: query "1408" → does cip start with "14.08"?
                    if "." not in query_lower:
                        # try inserting dot: "1408" → "14.08"
                        pass  # handled below
                    if not cip_code.replace(".", "").startswith(query_lower.replace(".", "")):
                        continue

                if cip_code == query_lower:
                    score = 0.99
                elif "." in query and cip_code.startswith(query):
                    # partial prefix: "14.08" matches "14.0801"
                    score = 0.95
                else:
                    score = 0.88
                match_type = "cip"
            # Tier 2: Keyword substring on cip_name
            elif query_lower in cip_name:
                score = 0.85 if cip_name.startswith(query_lower) else 0.75
                match_type = "keyword"
            elif query_lower in broad_lower:
                score = 0.60
                match_type = "keyword"
            # Tier 3: Fuzzy
            else:
                ratio = SequenceMatcher(None, query_lower, cip_name).ratio()
                if ratio < 0.40:
                    continue
                score = round(ratio * 0.55, 4)
                match_type = "fuzzy"
        else:
            # Broad-field candidate
            if is_cip:
                continue
            if query_lower in broad_lower:
                score = 0.55
                match_type = "keyword"
            else:
                ratio = SequenceMatcher(None, query_lower, broad_lower).ratio()
                if ratio < 0.40:
                    continue
                score = round(ratio * 0.45, 4)
                match_type = "fuzzy"

        scored.append({
            "score": score,
            "cip_code": cand["cip_code"],
            "cip_name": cand["cip_name"],
            "broad_field": cand["broad_field"],
            "subfield": cand["subfield"],
            "display_name": cand["display_name"],
            "match_type": match_type,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:MAX_RESULTS]
