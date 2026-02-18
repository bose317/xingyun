"""Comprehensive CIP (Classification of Instructional Programs) code tables.

Source: Statistics Canada CIP Canada 2021 Version 1.0
File:   cip-2021-structure.csv (downloaded from statcan.gc.ca)

Provides three levels:
  - Level 1 (series):    2-digit  "XX"       — 50 entries
  - Level 2 (subseries): 4-digit  "XX.XX"    — 454 entries
  - Level 3 (class):     6-digit  "XX.XXXX"  — 2119 entries
"""

import csv
import os

_CSV_PATH = os.path.join(os.path.dirname(__file__), "cip-2021-structure.csv")

# 2-digit CIP series → broad field name used in config.FIELD_OPTIONS
CIP_TO_BROAD: dict[str, str] = {
    "01": "Agriculture, natural resources and conservation",
    "03": "Agriculture, natural resources and conservation",
    "04": "Architecture, engineering, and related trades",
    "05": "Social and behavioural sciences and law",
    "09": "Social and behavioural sciences and law",
    "10": "Visual and performing arts, and communications technologies",
    "11": "Mathematics, computer and information sciences",
    "12": "Personal, protective and transportation services",
    "13": "Education",
    "14": "Architecture, engineering, and related trades",
    "15": "Architecture, engineering, and related trades",
    "16": "Humanities",
    "19": "Social and behavioural sciences and law",
    "22": "Social and behavioural sciences and law",
    "23": "Humanities",
    "24": "Humanities",
    "25": "Mathematics, computer and information sciences",
    "26": "Physical and life sciences and technologies",
    "27": "Mathematics, computer and information sciences",
    "29": "Architecture, engineering, and related trades",
    "30": "Physical and life sciences and technologies",
    "31": "Health and related fields",
    "38": "Humanities",
    "39": "Humanities",
    "40": "Physical and life sciences and technologies",
    "41": "Physical and life sciences and technologies",
    "42": "Social and behavioural sciences and law",
    "43": "Personal, protective and transportation services",
    "44": "Business, management and public administration",
    "45": "Social and behavioural sciences and law",
    "46": "Architecture, engineering, and related trades",
    "47": "Architecture, engineering, and related trades",
    "48": "Architecture, engineering, and related trades",
    "49": "Personal, protective and transportation services",
    "50": "Visual and performing arts, and communications technologies",
    "51": "Health and related fields",
    "52": "Business, management and public administration",
    "54": "Humanities",
    "55": "Humanities",
    "60": "Health and related fields",
    "61": "Health and related fields",
}


def _load_csv() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Parse the official CIP 2021 structure CSV into three dicts."""
    series: dict[str, str] = {}
    subseries: dict[str, str] = {}
    classes: dict[str, str] = {}

    with open(_CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            code = row["Code"].strip().rstrip(".")
            title = row["Class title"].strip()
            level = row["Level"].strip()
            if level == "1":
                series[code] = title
            elif level == "2":
                subseries[code] = title
            elif level == "3":
                classes[code] = title

    return series, subseries, classes


# Loaded once at import time
CIP_SERIES, CIP_SUBSERIES, CIP_CODES = _load_csv()
