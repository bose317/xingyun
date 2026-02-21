"""Configuration: API endpoints, table IDs, dimension mappings."""

API_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest/"

# Table keys → 8-digit Product IDs
TABLES = {
    "labour_force": 98100445,
    "income": 98100409,
    "unemployment_trends": 14100020,
    "job_vacancies": 14100443,
    "graduate_outcomes": 37100283,
    "graduate_outcomes_cip": 37100280,
    "cip_noc_distribution": 98100403,
    "noc_income": 98100412,
}

# ── Table 98100445: Labour force status ──
# Dims: Geo(174), Education(16), LocationOfStudy(7), Age(15), Gender(3), FieldOfStudy(63), LabourForceStatus(8)
# Coordinates: {geo}.{edu}.{loc}.{age}.{gender}.{field}.{status}.0.0.0

LABOUR_FORCE_GEO = {
    "Canada": 1, "Newfoundland and Labrador": 2, "Prince Edward Island": 7,
    "Nova Scotia": 10, "New Brunswick": 16, "Quebec": 26, "Ontario": 56,
    "Manitoba": 104, "Saskatchewan": 111, "Alberta": 121,
    "British Columbia": 141, "Yukon": 170, "Northwest Territories": 172, "Nunavut": 174,
}

LABOUR_FORCE_EDU = {
    "Total": 1, "No certificate, diploma or degree": 2,
    "High school diploma": 3, "Postsecondary certificate, diploma or degree": 4,
    "Below bachelor level": 5,
    "Apprenticeship or trades certificate or diploma": 6,
    "College, CEGEP or other non-university certificate or diploma": 9,
    "University certificate or diploma below bachelor level": 10,
    "Bachelor's degree or higher": 11, "Bachelor's degree": 12,
    "University certificate or diploma above bachelor level": 13,
    "Degree in medicine, dentistry, veterinary medicine or optometry": 14,
    "Master's degree": 15, "Earned doctorate": 16,
}

# Field of study member IDs (broad categories)
LABOUR_FORCE_FIELDS = {
    "Total": 1,
    "Education": 3,
    "Visual and performing arts, and communications technologies": 5,
    "Humanities": 8,
    "Social and behavioural sciences and law": 17,
    "Business, management and public administration": 25,
    "Physical and life sciences and technologies": 29,
    "Mathematics, computer and information sciences": 35,
    "Architecture, engineering, and related trades": 40,
    "Agriculture, natural resources and conservation": 48,
    "Health and related fields": 51,
    "Personal, protective and transportation services": 57,
}

# Detailed subfields (2-digit CIP mapped to member IDs)
LABOUR_FORCE_SUBFIELDS = {
    # Education
    "13. Education": 4,
    # Visual and performing arts
    "10. Communications technologies": 6,
    "50. Visual and performing arts": 7,
    # Humanities
    "16. Indigenous and foreign languages": 9,
    "23. English language and literature": 10,
    "24. Liberal arts and sciences": 11,
    "38. Philosophy and religious studies": 13,
    "39. Theology and religious vocations": 14,
    "54. History": 15,
    "55. French language and literature": 16,
    # Social and behavioural sciences and law
    "05. Area, ethnic, cultural, gender studies": 18,
    "09. Communication, journalism": 19,
    "22. Legal professions and studies": 21,
    "42. Psychology": 23,
    "45. Social sciences": 24,
    # Business
    "44. Public administration": 27,
    "52. Business, management, marketing": 28,
    # Physical and life sciences
    "26. Biological and biomedical sciences": 30,
    "40. Physical sciences": 33,
    "41. Science technologies": 34,
    # Math, CS
    "11. Computer and information sciences": 36,
    "25. Library science": 37,
    "27. Mathematics and statistics": 38,
    # Engineering
    "04. Architecture": 41,
    "14. Engineering": 42,
    "15. Engineering technologies": 43,
    "46. Construction trades": 45,
    "47. Mechanic and repair technologies": 46,
    "48. Precision production": 47,
    # Agriculture
    "01. Agricultural and veterinary sciences": 49,
    "03. Natural resources and conservation": 50,
    # Health
    "31. Parks, recreation, leisure, fitness": 53,
    "51. Health professions": 54,
    # Personal, protective
    "12. Culinary, entertainment, personal services": 58,
    "43. Security and protective services": 61,
    "49. Transportation and materials moving": 62,
}

LABOUR_FORCE_STATUS = {
    "Participation rate": 6,
    "Employment rate": 7,
    "Unemployment rate": 8,
    "In the labour force": 2,
    "Employed": 3,
    "Unemployed": 4,
}

# ── Table 98100409: Income ──
# Dims: Geo(14), Gender(3), Age(15), Education(16), WorkActivity(5), IncomeYear(2), FieldOfStudy(500), IncomeStats(7)
# Coordinates: {geo}.{gender}.{age}.{edu}.{work}.{year}.{field}.{stat}.0.0

INCOME_GEO = {
    "Canada": 1, "Newfoundland and Labrador": 2, "Prince Edward Island": 3,
    "Nova Scotia": 4, "New Brunswick": 5, "Quebec": 6, "Ontario": 7,
    "Manitoba": 8, "Saskatchewan": 9, "Alberta": 10,
    "British Columbia": 11, "Yukon": 12, "Northwest Territories": 13, "Nunavut": 14,
}

# Same education IDs as labour force (they share the same 16-member dimension)
INCOME_EDU = LABOUR_FORCE_EDU

# Broad field member IDs in the income table (500-member dimension)
INCOME_FIELDS = {
    "Total": 1,
    "Education": 3,
    "Visual and performing arts, and communications technologies": 20,
    "Humanities": 38,
    "Social and behavioural sciences and law": 97,
    "Business, management and public administration": 163,
    "Physical and life sciences and technologies": 195,
    "Mathematics, computer and information sciences": 241,
    "Architecture, engineering, and related trades": 273,
    "Agriculture, natural resources and conservation": 371,
    "Health and related fields": 399,
    "Personal, protective and transportation services": 476,
}

INCOME_SUBFIELDS = {
    # Math, CS detailed
    "11. Computer and information sciences": 242,
    "11.07 Computer science": 249,
    "11.02 Computer programming": 244,
    "11.04 Information science/studies": 246,
    "11.09 Computer systems networking": 251,
    "11.10 Computer/IT administration": 252,
    "25. Library science": 254,
    "27. Mathematics and statistics": 258,
    "27.01 Mathematics": 259,
    "27.05 Statistics": 261,
    "30.70 Data science": 271,
    "30.71 Data analytics": 272,
    # Engineering
    "04. Architecture": 274,
    "14. Engineering": 284,
    "14.07 Chemical engineering": 291,
    "14.08 Civil engineering": 292,
    "14.09 Computer engineering": 293,
    "14.10 Electrical engineering": 294,
    "14.19 Mechanical engineering": 300,
    "15. Engineering technologies": 326,
    # Health
    "51. Health professions": 407,
    "51.12 Medicine": 419,
    "51.38 Nursing": 436,
    "51.20 Pharmacy": 424,
    # Business
    "52. Business, management, marketing": 172,
    "52.01 Business/commerce, general": 173,
    "52.03 Accounting": 175,
    "52.08 Finance": 180,
    "52.14 Marketing": 186,
    # Education
    "13. Education": 4,
    # Social sciences
    "22. Legal professions (Law)": 119,
    "42. Psychology": 143,
    "45. Social sciences": 148,
    "45.06 Economics": 154,
}

INCOME_STATS = {
    "Median employment income": 3,
    "Average employment income": 4,
    "Median wages, salaries and commissions": 6,
    "Average wages, salaries and commissions": 7,
}

# ── Table 14100020: Unemployment trends ──
# Dims: Geo(11), LabourForce(10), Education(9), Gender(3), AgeGroup(9)
# Coordinates: {geo}.{lf}.{edu}.{gender}.{age}.0.0.0.0.0

UNEMP_GEO = {
    "Canada": 1, "Newfoundland and Labrador": 2, "Prince Edward Island": 3,
    "Nova Scotia": 4, "New Brunswick": 5, "Quebec": 6, "Ontario": 7,
    "Manitoba": 8, "Saskatchewan": 9, "Alberta": 10, "British Columbia": 11,
}

UNEMP_INDICATOR = {
    "Unemployment rate": 8,
    "Participation rate": 9,
    "Employment rate": 10,
}

UNEMP_EDU = {
    "Total, all education levels": 1,
    "0 to 8 years": 2,
    "Some high school": 3,
    "High school graduate": 4,
    "Some postsecondary": 5,
    "Postsecondary certificate or diploma": 6,
    "University degree": 7,
    "Bachelor's degree": 8,
    "Above bachelor's degree": 9,
}

# ── Table 14100443: Job vacancies ──
# Dims: Geo(14), NOC(824), Characteristics(48), Statistics(3)
# Coordinates: {geo}.{noc}.{char}.{stat}.0.0.0.0.0.0

JOB_VAC_GEO = INCOME_GEO

JOB_VAC_CHAR = {
    "All types": 1,
    "No minimum education required": 5,
    "High school diploma or equivalent": 6,
    "Non-university certificate or diploma": 7,
    "Trade certificate or diploma": 8,
    "College, CEGEP certificate or diploma": 9,
    "University certificate below bachelor's": 10,
    "Bachelor's degree": 12,
    "Above bachelor's degree": 13,
}

JOB_VAC_STAT = {
    "Job vacancies": 1,
    "Proportion of job vacancies": 2,
    "Average offered hourly wage": 5,
}

# ── Table 37100283: Graduate outcomes ──
# Dims: Geo(12), EduQualification(13), Field(41), Gender(3), AgeGroup(3), StudentStatus(3), Characteristics(5), Stats(3)
# Coordinates: {geo}.{qual}.{field}.{gender}.{age}.{status}.{char}.{stat}.0.0

GRAD_GEO = {
    "Canada": 1, "Newfoundland and Labrador": 2, "Prince Edward Island": 3,
    "Nova Scotia": 4, "New Brunswick": 5, "Quebec": 6, "Ontario": 7,
    "Manitoba": 8, "Saskatchewan": 9, "Alberta": 10,
    "British Columbia": 11, "Territories": 12,
}

GRAD_QUAL = {
    "Total": 1,
    "Short credential": 2,
    "Certificate": 3,
    "Diploma": 4,
    "Undergraduate certificate": 6,
    "Undergraduate degree": 7,
    "Professional degree": 9,
    "Master's degree": 11,
    "Doctoral degree": 12,
}

GRAD_FIELDS = {
    "Total": 1,
    "STEM": 2,
    "Science and science technology": 3,
    "Engineering and engineering technology": 7,
    "Mathematics and computer and information science": 10,
    "Computer and information science": 12,
    "BHASE": 13,
    "Business and administration": 14,
    "Arts and humanities": 17,
    "Social and behavioural sciences": 20,
    "Legal professions and studies": 25,
    "Health care": 28,
    "Education and teaching": 33,
    "Trades, services, natural resources and conservation": 35,
}

GRAD_STATS = {
    "Number of graduates": 1,
    "Median income 2yr after graduation": 2,
    "Median income 5yr after graduation": 3,
}

# ── UI Dropdown Mappings ──

# Maps user-friendly field names → (labour_force_member_id, income_member_id, grad_field_id)
FIELD_OPTIONS = {
    "Education": {
        "labour_force": 3, "income": 3, "graduate": 33,
        "subfields": {
            "13. Education": {"labour_force": 4, "income": 4},
        },
    },
    "Visual and performing arts, and communications technologies": {
        "labour_force": 5, "income": 20, "graduate": 17,
        "subfields": {
            "10. Communications technologies": {"labour_force": 6, "income": 21},
            "50. Visual and performing arts": {"labour_force": 7, "income": 26},
        },
    },
    "Humanities": {
        "labour_force": 8, "income": 38, "graduate": 19,
        "subfields": {
            "23. English language and literature": {"labour_force": 10, "income": 59},
            "38. Philosophy and religious studies": {"labour_force": 13, "income": 76},
            "54. History": {"labour_force": 15, "income": 90},
        },
    },
    "Social and behavioural sciences and law": {
        "labour_force": 17, "income": 97, "graduate": 20,
        "subfields": {
            "22. Legal professions (Law)": {"labour_force": 21, "income": 119},
            "42. Psychology": {"labour_force": 23, "income": 143},
            "45. Social sciences": {"labour_force": 24, "income": 148},
            "45.06 Economics": {"income": 154},
            "09. Communication, journalism": {"labour_force": 19, "income": 102},
        },
    },
    "Business, management and public administration": {
        "labour_force": 25, "income": 163, "graduate": 14,
        "subfields": {
            "52. Business, management, marketing": {"labour_force": 28, "income": 172},
            "52.01 Business/commerce, general": {"income": 173},
            "52.03 Accounting": {"income": 175},
            "52.08 Finance": {"income": 180},
            "52.14 Marketing": {"income": 186},
            "44. Public administration": {"labour_force": 27, "income": 165},
        },
    },
    "Physical and life sciences and technologies": {
        "labour_force": 29, "income": 195, "graduate": 3,
        "subfields": {
            "26. Biological and biomedical sciences": {"labour_force": 30, "income": 196},
            "40. Physical sciences": {"labour_force": 33, "income": 225},
        },
    },
    "Mathematics, computer and information sciences": {
        "labour_force": 35, "income": 241, "graduate": 10,
        "subfields": {
            "11. Computer and information sciences": {"labour_force": 36, "income": 242},
            "11.02 Computer programming": {"income": 244},
            "11.04 Information science/studies": {"income": 246},
            "11.07 Computer science": {"income": 249},
            "11.09 Computer systems networking": {"income": 251},
            "11.10 Computer/IT administration": {"income": 252},
            "27. Mathematics and statistics": {"labour_force": 38, "income": 258},
            "27.01 Mathematics": {"income": 259},
            "27.05 Statistics": {"income": 261},
            "30.70 Data science": {"income": 271},
            "30.71 Data analytics": {"income": 272},
        },
    },
    "Architecture, engineering, and related trades": {
        "labour_force": 40, "income": 273, "graduate": 7,
        "subfields": {
            "04. Architecture": {"labour_force": 41, "income": 274},
            "14. Engineering": {"labour_force": 42, "income": 284},
            "14.07 Chemical engineering": {"income": 291},
            "14.08 Civil engineering": {"income": 292},
            "14.09 Computer engineering": {"income": 293},
            "14.10 Electrical engineering": {"income": 294},
            "14.19 Mechanical engineering": {"income": 300},
            "15. Engineering technologies": {"labour_force": 43, "income": 326},
        },
    },
    "Agriculture, natural resources and conservation": {
        "labour_force": 48, "income": 371, "graduate": 36,
        "subfields": {
            "01. Agricultural and veterinary sciences": {"labour_force": 49, "income": 372},
            "03. Natural resources and conservation": {"labour_force": 50, "income": 392},
        },
    },
    "Health and related fields": {
        "labour_force": 51, "income": 399, "graduate": 28,
        "subfields": {
            "51. Health professions": {"labour_force": 54, "income": 407},
            "51.12 Medicine": {"income": 419},
            "51.20 Pharmacy": {"income": 424},
            "51.38 Nursing": {"income": 436},
            "31. Parks, recreation, leisure, fitness": {"labour_force": 53, "income": 401},
        },
    },
    "Personal, protective and transportation services": {
        "labour_force": 57, "income": 476, "graduate": 38,
        "subfields": {
            "12. Culinary, entertainment, personal services": {"labour_force": 58, "income": 477},
            "43. Security and protective services": {"labour_force": 61, "income": 487},
        },
    },
}

EDUCATION_OPTIONS = {
    "Bachelor's degree": {
        "labour_force": 12, "income": 12, "unemp": 8, "job_vac": 12, "grad": 7,
    },
    "Master's degree": {
        "labour_force": 15, "income": 15, "unemp": 9, "job_vac": 13, "grad": 11,
    },
    "Earned doctorate": {
        "labour_force": 16, "income": 16, "unemp": 9, "grad": 12,
    },
    "College, CEGEP or other non-university certificate or diploma": {
        "labour_force": 9, "income": 9, "unemp": 6, "job_vac": 9, "grad": 4,
    },
    "Apprenticeship or trades certificate or diploma": {
        "labour_force": 6, "income": 6, "unemp": 6, "job_vac": 8, "grad": 3,
    },
    "High school diploma": {
        "labour_force": 3, "income": 3, "unemp": 4, "job_vac": 6,
    },
    "Degree in medicine, dentistry, veterinary medicine or optometry": {
        "labour_force": 14, "income": 14, "unemp": 9, "grad": 9,
    },
    "University degree (any)": {
        "labour_force": 11, "income": 11, "unemp": 7,
    },
}

GEO_OPTIONS = [
    "Canada", "Newfoundland and Labrador", "Prince Edward Island",
    "Nova Scotia", "New Brunswick", "Quebec", "Ontario",
    "Manitoba", "Saskatchewan", "Alberta", "British Columbia",
    "Yukon", "Northwest Territories", "Nunavut",
]

# ── Table 37100280: Graduate outcomes by CIP primary groupings ──
# Dims: Geo(12), EduQualification(13), Field(64), Gender(3), AgeGroup(3),
#        StudentStatus(3), Characteristics(5), Stats(3)
# Coordinates: {geo}.{qual}.{field}.{gender}.{age}.{status}.{char}.{stat}.0.0

GRAD_CIP_GEO = {
    "Canada": 1, "Newfoundland and Labrador": 2, "Prince Edward Island": 3,
    "Nova Scotia": 4, "New Brunswick": 5, "Quebec": 6, "Ontario": 7,
    "Manitoba": 8, "Saskatchewan": 9, "Alberta": 10,
    "British Columbia": 11, "Territories": 12,
}

GRAD_CIP_QUAL = {
    "Total": 1,
    "Short credential": 2,
    "Certificate": 3,
    "Diploma": 4,
    "Undergraduate certificate": 6,
    "Undergraduate degree": 7,
    "Professional degree": 9,
    "Master's degree": 11,
    "Doctoral degree": 12,
}

GRAD_CIP_STATS = {
    "Number of graduates": 1,
    "Median income 2yr after graduation": 2,
    "Median income 5yr after graduation": 3,
}

# CIP-based field of study member IDs (broad categories = parent nodes)
GRAD_CIP_BROAD_FIELDS = {
    "Total": 1,
    "Education": 2,
    "Visual and performing arts, and communications technologies": 4,
    "Humanities": 7,
    "Social and behavioural sciences and law": 16,
    "Business, management and public administration": 24,
    "Physical and life sciences and technologies": 28,
    "Mathematics, computer and information sciences": 34,
    "Architecture, engineering, and related trades": 39,
    "Agriculture, natural resources and conservation": 47,
    "Health and related fields": 50,
    "Personal, protective and transportation services": 56,
    "Other instructional programs": 62,
}

# Detailed CIP sub-fields (2-digit CIP → member IDs)
GRAD_CIP_SUBFIELDS = {
    # Education
    "13. Education": 3,
    # Visual and performing arts
    "10. Communications technologies": 5,
    "50. Visual and performing arts": 6,
    # Humanities
    "16. Indigenous and foreign languages": 8,
    "23. English language and literature": 9,
    "24. Liberal arts and sciences": 10,
    "30A. Interdisciplinary humanities": 11,
    "38. Philosophy and religious studies": 12,
    "39. Theology and religious vocations": 13,
    "54. History": 14,
    "55. French language and literature": 15,
    # Social and behavioural sciences and law
    "05. Area, ethnic, cultural, gender studies": 17,
    "09. Communication, journalism": 18,
    "19. Family and consumer sciences": 19,
    "22. Legal professions and studies": 20,
    "30B. Interdisciplinary social and behavioural sciences": 21,
    "42. Psychology": 22,
    "45. Social sciences": 23,
    # Business
    "30.16 Accounting and computer science": 25,
    "44. Public administration": 26,
    "52. Business, management, marketing": 27,
    # Physical and life sciences
    "26. Biological and biomedical sciences": 29,
    "30.01 Biological and physical sciences": 30,
    "30C. Other interdisciplinary physical and life sciences": 31,
    "40. Physical sciences": 32,
    "41. Science technologies": 33,
    # Math, CS
    "11. Computer and information sciences": 35,
    "25. Library science": 36,
    "27. Mathematics and statistics": 37,
    "30D. Interdisciplinary math, CS": 38,
    # Engineering
    "04. Architecture": 40,
    "14. Engineering": 41,
    "15. Engineering technologies": 42,
    "30.12 Historic preservation": 43,
    "46. Construction trades": 44,
    "47. Mechanic and repair technologies": 45,
    "48. Precision production": 46,
    # Agriculture
    "01. Agricultural and veterinary sciences": 48,
    "03. Natural resources and conservation": 49,
    # Health
    "30.37 Design for human health": 51,
    "31. Parks, recreation, leisure, fitness": 52,
    "51. Health professions": 53,
    "60. Health professions residency": 54,
    "61. Medical residency": 55,
    # Personal, protective
    "12. Culinary, entertainment, personal services": 57,
    "28. Military science": 58,
    "29. Military technologies": 59,
    "43. Security and protective services": 60,
    "49. Transportation and materials moving": 61,
    # Other
    "30.00 Inclusive postsecondary education": 63,
    "30.99 Multidisciplinary studies, other": 64,
}

# Map 2-digit CIP prefix → member ID in table 37100280
# Used to resolve a user's 6-digit CIP to the closest sub-field in this table
CIP_PREFIX_TO_GRAD_CIP = {
    "13": 3,   # Education
    "10": 5,   # Communications technologies
    "50": 6,   # Visual and performing arts
    "16": 8,   # Indigenous and foreign languages
    "23": 9,   # English language and literature
    "24": 10,  # Liberal arts and sciences
    "38": 12,  # Philosophy and religious studies
    "39": 13,  # Theology and religious vocations
    "54": 14,  # History
    "55": 15,  # French language and literature
    "05": 17,  # Area, ethnic, cultural, gender studies
    "09": 18,  # Communication, journalism
    "19": 19,  # Family and consumer sciences
    "22": 20,  # Legal professions and studies
    "42": 22,  # Psychology
    "45": 23,  # Social sciences
    "44": 26,  # Public administration
    "52": 27,  # Business, management, marketing
    "26": 29,  # Biological and biomedical sciences
    "40": 32,  # Physical sciences
    "41": 33,  # Science technologies
    "11": 35,  # Computer and information sciences
    "25": 36,  # Library science
    "27": 37,  # Mathematics and statistics
    "04": 40,  # Architecture
    "14": 41,  # Engineering
    "15": 42,  # Engineering technologies
    "46": 44,  # Construction trades
    "47": 45,  # Mechanic and repair technologies
    "48": 46,  # Precision production
    "01": 48,  # Agricultural and veterinary sciences
    "03": 49,  # Natural resources and conservation
    "31": 52,  # Parks, recreation, leisure, fitness
    "51": 53,  # Health professions
    "12": 57,  # Culinary, entertainment, personal services
    "28": 58,  # Military science
    "29": 59,  # Military technologies
    "43": 60,  # Security and protective services
    "49": 61,  # Transportation and materials moving
}

# ── Table 98100403: Occupation by major field of study (CIP→NOC) ──
# Dims: Geo(1), Age(4), CIP(500), Education(16), Gender(3), NOC(821), Statistics(6)
# Coordinates: {geo}.{age}.{cip}.{edu}.{gender}.{noc}.{stat}.0.0.0
# This table provides count and % distribution of graduates by NOC occupation

# CIP field IDs in table 98100403 (same as INCOME_FIELDS — they share the CIP 2021 500-member dim)
NOC_DIST_CIP_FIELDS = {
    "Total": 1,
    "Education": 3,
    "Visual and performing arts, and communications technologies": 20,
    "Humanities": 38,
    "Social and behavioural sciences and law": 97,
    "Business, management and public administration": 163,
    "Physical and life sciences and technologies": 195,
    "Mathematics, computer and information sciences": 241,
    "Architecture, engineering, and related trades": 273,
    "Agriculture, natural resources and conservation": 371,
    "Health and related fields": 399,
    "Personal, protective and transportation services": 476,
}

# 2-digit CIP → member IDs in table 98100403 (same as income table)
NOC_DIST_CIP_SUBFIELDS = {
    "13": 4,    # Education
    "10": 21,   # Communications technologies
    "50": 26,   # Visual and performing arts
    "16": 39,   # Indigenous and foreign languages
    "23": 59,   # English language and literature
    "24": 64,   # Liberal arts and sciences
    "38": 76,   # Philosophy and religious studies
    "39": 81,   # Theology and religious vocations
    "54": 90,   # History
    "55": 92,   # French language and literature
    "05": 98,   # Area, ethnic, cultural, gender studies
    "09": 102,  # Communication, journalism
    "19": 109,  # Family and consumer sciences
    "22": 119,  # Legal professions and studies
    "42": 143,  # Psychology
    "45": 148,  # Social sciences
    "44": 165,  # Public administration
    "52": 172,  # Business, management, marketing
    "26": 196,  # Biological and biomedical sciences
    "40": 225,  # Physical sciences
    "41": 235,  # Science technologies
    "11": 242,  # Computer and information sciences
    "25": 254,  # Library science
    "27": 258,  # Mathematics and statistics
    "04": 274,  # Architecture
    "14": 284,  # Engineering
    "15": 326,  # Engineering technologies
    "46": 347,  # Construction trades
    "47": 355,  # Mechanic and repair technologies
    "48": 364,  # Precision production
    "01": 372,  # Agricultural and veterinary sciences
    "03": 392,  # Natural resources and conservation
    "31": 401,  # Parks, recreation, leisure, fitness
    "51": 407,  # Health professions
    "12": 477,  # Culinary, entertainment, personal services
    "28": 483,  # Military science
    "29": 485,  # Military technologies
    "43": 487,  # Security and protective services
    "49": 493,  # Transportation and materials moving
}

# NOC 2021 broad occupation categories (1-digit level)
NOC_BROAD_CATEGORIES = {
    "0 Legislative and senior management": 4,
    "1 Business, finance and administration": 10,
    "2 Natural and applied sciences": 105,
    "3 Health occupations": 202,
    "4 Education, law, social and government services": 268,
    "5 Art, culture, recreation and sport": 358,
    "6 Sales and service": 422,
    "7 Trades, transport and equipment operators": 527,
    "8 Natural resources, agriculture and production": 671,
    "9 Manufacturing and utilities": 725,
}

# NOC 2-digit sub-major groups
NOC_SUBMAJOR_GROUPS = {
    # Under 0
    "00 Legislative and senior managers": 5,
    # Under 1
    "10 Specialized middle management (admin/finance/business)": 11,
    "11 Professional occupations in finance and business": 25,
    "12 Administrative/financial supervisors and specialized admin": 38,
    "13 Administrative and transportation logistics": 63,
    "14 Administrative/financial support and supply chain": 77,
    # Under 2
    "20 Specialized middle management (engineering/science/IT)": 106,
    "21 Professional occupations in natural and applied sciences": 112,
    "22 Technical occupations in natural and applied sciences": 164,
    # Under 3
    "30 Specialized middle management (health care)": 203,
    "31 Professional occupations in health": 207,
    "32 Technical occupations in health": 235,
    "33 Assisting occupations in health services": 260,
    # Under 4
    "40 Managers in public admin, education, social services": 269,
    "41 Professional occupations in law, education, social services": 285,
    "42 Front-line public protection and paraprofessional": 321,
    "43 Assisting occupations in education and legal": 334,
    "44 Care providers and legal/public protection support": 346,
    "45 Student monitors, crossing guards and related": 354,
    # Under 5
    "50 Specialized middle management (art/culture/recreation)": 359,
    "51 Professional occupations in art and culture": 365,
    "52 Technical occupations in art, culture and sport": 381,
    "53 Occupations in art, culture and sport": 395,
    "54 Support occupations in sport": 414,
    "55 Support occupations in art and culture": 418,
    # Under 6
    "60 Middle management (retail/wholesale/customer services)": 423,
    "62 Retail sales and service supervisors": 434,
    "63 Occupations in sales and services": 454,
    "64 Sales/service reps and personal services": 471,
    "65 Sales and service support": 501,
    # Under 7
    "70 Middle management (trades/transportation)": 528,
    "72 Technical trades and transportation officers": 537,
    "73 General trades": 612,
    "74 Mail/message distribution and other transport": 641,
    "75 Helpers, labourers and transport drivers": 655,
    # Under 8
    "80 Middle management (production/agriculture)": 672,
    "82 Supervisors in natural resources/agriculture": 680,
    "83 Occupations in natural resources and production": 690,
    "84 Workers in natural resources/agriculture": 700,
    "85 Harvesting, landscaping and labourers": 711,
    # Under 9
    "90 Middle management (manufacturing/utilities)": 726,
    "92 Processing/manufacturing supervisors": 731,
    "93 Central control and process operators": 750,
    "94 Machine operators, assemblers and inspectors": 759,
    "95 Labourers in processing/manufacturing": 810,
}

NOC_DIST_STATS = {
    "pct_distribution": 1,
    "count": 4,
}

# 2-digit NOC → list of 5-digit children member IDs (for drill-down queries)
NOC_2DIGIT_TO_5DIGIT = {
    5: [8, 9],
    11: [14, 15, 16, 17, 19, 20, 21, 22, 24],
    25: [28, 29, 30, 31, 32, 35, 36, 37],
    38: [41, 42, 43, 44, 47, 48, 49, 50, 51, 53, 54, 55, 56, 59, 60, 61, 62],
    63: [66, 67, 68, 70, 71, 72, 75, 76],
    77: [80, 81, 82, 83, 85, 86, 87, 90, 91, 92, 95, 96, 99, 100, 101, 102, 103, 104],
    106: [109, 110, 111],
    112: [115, 116, 117, 118, 119, 121, 122, 123, 125, 128, 129, 130, 131, 133, 134, 136, 137, 138, 139, 141, 142, 143, 144, 145, 148, 149, 151, 152, 154, 155, 156, 158, 159, 160, 162, 163],
    164: [167, 168, 170, 171, 172, 173, 174, 177, 178, 179, 180, 181, 183, 184, 185, 187, 188, 189, 190, 193, 194, 195, 196, 198, 199, 200, 201],
    203: [206],
    207: [210, 211, 212, 213, 215, 216, 217, 219, 220, 223, 224, 225, 226, 227, 228, 231, 232, 233, 234],
    235: [238, 239, 240, 241, 242, 243, 245, 246, 247, 249, 250, 251, 252, 253, 254, 257, 258, 259],
    260: [263, 264, 265, 266, 267],
    269: [272, 273, 274, 275, 277, 278, 280, 282, 283, 284],
    285: [288, 289, 292, 293, 295, 297, 298, 301, 302, 303, 305, 306, 308, 309, 312, 313, 314, 315, 316, 317, 318, 319, 320],
    321: [324, 325, 326, 329, 330, 331, 332, 333],
    334: [337, 338, 341, 342, 343, 344, 345],
    346: [349, 350, 353],
    354: [357],
    359: [362, 363, 364],
    365: [368, 369, 370, 372, 373, 374, 375, 376, 378, 379, 380],
    381: [384, 386, 387, 388, 389, 390, 391, 393, 394],
    395: [398, 400, 401, 403, 404, 405, 406, 407, 408, 411, 412, 413],
    414: [417],
    418: [421],
    423: [426, 428, 430, 431, 433],
    434: [437, 439, 440, 441, 442, 443, 444, 447, 448, 451, 452, 453],
    454: [457, 458, 459, 462, 463, 464, 466, 467, 469, 470],
    471: [474, 475, 478, 479, 482, 483, 485, 486, 487, 488, 489, 491, 492, 493, 496, 497, 498, 500],
    501: [504, 505, 506, 507, 510, 511, 512, 514, 515, 517, 518, 521, 522, 523, 525, 526],
    528: [531, 532, 533, 535, 536],
    537: [540, 541, 542, 543, 544, 546, 547, 548, 549, 550, 551, 554, 555, 556, 557, 558, 559, 560, 563, 564, 565, 566, 567, 568, 571, 572, 573, 575, 576, 578, 579, 582, 583, 584, 585, 586, 587, 588, 590, 591, 593, 594, 595, 596, 597, 600, 601, 604, 605, 606, 607, 608, 611],
    612: [615, 616, 617, 619, 620, 621, 622, 625, 626, 627, 628, 631, 632, 634, 635, 638, 639, 640],
    641: [644, 645, 646, 649, 650, 651, 652, 653, 654],
    655: [658, 659, 661, 662, 665, 666, 668, 669, 670],
    672: [675, 677, 678, 679],
    680: [683, 685, 686, 688, 689],
    690: [693, 694, 696, 698, 699],
    700: [703, 704, 706, 707, 709, 710],
    711: [714, 715, 716, 717, 718, 720, 721, 723, 724],
    726: [729, 730],
    731: [734, 735, 736, 737, 738, 739, 741, 742, 743, 744, 745, 748, 749],
    750: [753, 754, 755, 758],
    759: [762, 763, 764, 765, 766, 767, 768, 769, 771, 772, 773, 775, 776, 777, 778, 779, 780, 782, 783, 784, 785, 787, 788, 789, 790, 792, 793, 794, 795, 798, 799, 800, 801, 802, 803, 805, 806, 807, 808, 809],
    810: [813, 814, 815, 816, 817, 818, 819, 820, 821],
}

# 5-digit NOC member ID → display name (NOC code + description)
NOC_5DIGIT_NAMES = {
    8: "00010 Legislators", 9: "00018 Senior managers",
    14: "10010 Financial managers", 15: "10011 Human resources managers",
    16: "10012 Purchasing managers", 17: "10019 Other administrative services managers",
    19: "10020 Insurance, real estate and financial brokerage managers", 20: "10021 Banking, credit and other investment managers",
    21: "10022 Advertising, marketing and public relations managers", 22: "10029 Other business services managers",
    24: "10030 Telecommunication carriers managers",
    28: "11100 Financial auditors and accountants", 29: "11101 Financial and investment analysts",
    30: "11102 Financial advisors", 31: "11103 Securities agents and investment dealers",
    32: "11109 Other financial officers", 35: "11200 Human resources professionals",
    36: "11201 Business management consulting", 37: "11202 Advertising, marketing and public relations",
    41: "12010 Supervisors, general office", 42: "12011 Supervisors, finance and insurance",
    43: "12012 Supervisors, library and correspondence", 44: "12013 Supervisors, supply chain and scheduling",
    47: "12100 Executive assistants", 48: "12101 Human resources and recruitment officers",
    49: "12102 Procurement and purchasing agents", 50: "12103 Conference and event planners",
    51: "12104 Employment insurance and revenue officers",
    53: "12110 Court reporters and medical transcriptionists", 54: "12111 Health information management",
    55: "12112 Records management technicians", 56: "12113 Statistical officers and research support",
    59: "12200 Accounting technicians and bookkeepers", 60: "12201 Insurance adjusters",
    61: "12202 Insurance underwriters", 62: "12203 Assessors and business valuators",
    66: "13100 Administrative officers", 67: "13101 Property administrators",
    68: "13102 Payroll administrators", 70: "13110 Administrative assistants",
    71: "13111 Legal administrative assistants", 72: "13112 Medical administrative assistants",
    75: "13200 Customs, ship and other brokers", 76: "13201 Production and transportation logistics coordinators",
    80: "14100 General office support workers", 81: "14101 Receptionists",
    82: "14102 Personnel clerks", 83: "14103 Court clerks",
    85: "14110 Survey interviewers and statistical clerks", 86: "14111 Data entry clerks",
    87: "14112 Desktop publishing operators",
    90: "14200 Accounting and related clerks", 91: "14201 Banking and insurance clerks",
    92: "14202 Collection clerks", 95: "14300 Library assistants and clerks",
    96: "14301 Correspondence and publication clerks",
    99: "14400 Shippers and receivers", 100: "14401 Storekeepers and partspersons",
    101: "14402 Production logistics workers", 102: "14403 Purchasing and inventory control workers",
    103: "14404 Dispatchers", 104: "14405 Transportation route schedulers",
    109: "20010 Engineering managers", 110: "20011 Architecture and science managers",
    111: "20012 Computer and information systems managers",
    115: "21100 Physicists and astronomers", 116: "21101 Chemists",
    117: "21102 Geoscientists and oceanographers", 118: "21103 Meteorologists",
    119: "21109 Other physical sciences professionals",
    121: "21110 Biologists and related scientists", 122: "21111 Forestry professionals",
    123: "21112 Agricultural representatives and specialists", 125: "21120 Public and environmental health professionals",
    128: "21200 Architects", 129: "21201 Landscape architects",
    130: "21202 Urban and land use planners", 131: "21203 Land surveyors",
    133: "21210 Mathematicians, statisticians and actuaries", 134: "21211 Data scientists",
    136: "21220 Cybersecurity specialists", 137: "21221 Business systems specialists",
    138: "21222 Information systems specialists", 139: "21223 Database analysts and data administrators",
    141: "21230 Computer systems developers and programmers", 142: "21231 Software engineers and designers",
    143: "21232 Software developers and programmers", 144: "21233 Web designers",
    145: "21234 Web developers and programmers",
    148: "21300 Civil engineers", 149: "21301 Mechanical engineers",
    151: "21310 Electrical and electronics engineers", 152: "21311 Computer engineers",
    154: "21320 Chemical engineers", 155: "21321 Industrial and manufacturing engineers",
    156: "21322 Metallurgical and materials engineers",
    158: "21330 Mining engineers", 159: "21331 Geological engineers", 160: "21332 Petroleum engineers",
    162: "21390 Aerospace engineers", 163: "21399 Other professional engineers",
    167: "22100 Chemical technologists", 168: "22101 Geological and mineral technologists",
    170: "22110 Biological technologists", 171: "22111 Agricultural and fish products inspectors",
    172: "22112 Forestry technologists", 173: "22113 Conservation and fishery officers",
    174: "22114 Landscape and horticulture technicians",
    177: "22210 Architectural technologists", 178: "22211 Industrial designers",
    179: "22212 Drafting technologists", 180: "22213 Land survey technologists",
    181: "22214 Technical occupations in geomatics and meteorology",
    183: "22220 Computer network and web technicians", 184: "22221 User support technicians",
    185: "22222 Information systems testing technicians",
    187: "22230 Non-destructive testers and inspectors", 188: "22231 Engineering inspectors",
    189: "22232 Occupational health and safety specialists", 190: "22233 Construction inspectors",
    193: "22300 Civil engineering technologists", 194: "22301 Mechanical engineering technologists",
    195: "22302 Industrial engineering technologists", 196: "22303 Construction estimators",
    198: "22310 Electrical and electronics engineering technologists",
    199: "22311 Electronic service technicians", 200: "22312 Industrial instrument technicians",
    201: "22313 Aircraft instrument and avionics mechanics",
    206: "30010 Managers in health care",
    210: "31100 Specialists in clinical and laboratory medicine", 211: "31101 Specialists in surgery",
    212: "31102 General practitioners and family physicians", 213: "31103 Veterinarians",
    215: "31110 Dentists", 216: "31111 Optometrists",
    217: "31112 Audiologists and speech-language pathologists",
    219: "31120 Pharmacists", 220: "31121 Dietitians and nutritionists",
    223: "31200 Psychologists", 224: "31201 Chiropractors", 225: "31202 Physiotherapists",
    226: "31203 Occupational therapists", 227: "31204 Kinesiologists",
    228: "31209 Other health diagnosing and treating professionals",
    231: "31300 Nursing coordinators and supervisors", 232: "31301 Registered nurses",
    233: "31302 Nurse practitioners", 234: "31303 Physician assistants and midwives",
    238: "32100 Opticians", 239: "32101 Licensed practical nurses",
    240: "32102 Paramedical occupations", 241: "32103 Respiratory therapists",
    242: "32104 Animal health technologists", 243: "32109 Other therapy and assessment technicians",
    245: "32110 Denturists", 246: "32111 Dental hygienists",
    247: "32112 Dental technologists", 249: "32120 Medical laboratory technologists",
    250: "32121 Medical radiation technologists", 251: "32122 Medical sonographers",
    252: "32123 Cardiology technologists", 253: "32124 Pharmacy technicians",
    254: "32129 Other medical technologists", 257: "32200 Traditional Chinese medicine practitioners",
    258: "32201 Massage therapists", 259: "32209 Other natural healing practitioners",
    263: "33100 Dental assistants", 264: "33101 Medical laboratory assistants",
    265: "33102 Nurse aides and orderlies", 266: "33103 Pharmacy assistants",
    267: "33109 Other health support occupations",
    272: "40010 Government managers - health and social policy", 273: "40011 Government managers - economic analysis",
    274: "40012 Government managers - education policy", 275: "40019 Other managers in public administration",
    277: "40020 Administrators - post-secondary education", 278: "40021 School principals and administrators",
    280: "40030 Managers in social and community services",
    282: "40040 Commissioned police officers", 283: "40041 Fire chiefs",
    284: "40042 Commissioned officers of the Canadian Armed Forces",
    288: "41100 Judges", 289: "41101 Lawyers and Quebec notaries",
    292: "41200 University professors and lecturers", 293: "41201 Post-secondary teaching/research assistants",
    295: "41210 College and vocational instructors",
    297: "41220 Secondary school teachers", 298: "41221 Elementary school and kindergarten teachers",
    301: "41300 Social workers", 302: "41301 Counselling therapists",
    303: "41302 Religious leaders", 305: "41310 Police investigators",
    306: "41311 Probation and parole officers", 308: "41320 Educational counsellors",
    309: "41321 Career development practitioners",
    312: "41400 Natural/applied science policy researchers", 313: "41401 Economists",
    314: "41402 Business development officers and market researchers",
    315: "41403 Social policy researchers", 316: "41404 Health policy researchers",
    317: "41405 Education policy researchers", 318: "41406 Recreation/sports policy researchers",
    319: "41407 Program officers unique to government", 320: "41409 Other social science professionals",
    324: "42100 Police officers", 325: "42101 Firefighters",
    326: "42102 Specialized members of the Canadian Armed Forces",
    329: "42200 Paralegals", 330: "42201 Social and community service workers",
    331: "42202 Early childhood educators", 332: "42203 Instructors of persons with disabilities",
    333: "42204 Religion workers",
    337: "43100 Teacher assistants", 338: "43109 Other instructors",
    341: "43200 Sheriffs and bailiffs", 342: "43201 Correctional service officers",
    343: "43202 By-law enforcement officers", 344: "43203 Border services and immigration officers",
    345: "43204 Operations members of the Canadian Armed Forces",
    349: "44100 Home child care providers", 350: "44101 Home support workers and caregivers",
    353: "44200 Primary combat members of the Canadian Armed Forces",
    357: "45100 Student monitors and crossing guards",
    362: "50010 Library, archive, museum and gallery managers",
    363: "50011 Managers - publishing, motion pictures, broadcasting",
    364: "50012 Recreation, sports and fitness program directors",
    368: "51100 Librarians", 369: "51101 Conservators and curators", 370: "51102 Archivists",
    372: "51110 Editors", 373: "51111 Authors and writers",
    374: "51112 Technical writers", 375: "51113 Journalists",
    376: "51114 Translators and interpreters",
    378: "51120 Producers, directors and choreographers",
    379: "51121 Conductors, composers and arrangers", 380: "51122 Musicians and singers",
    384: "52100 Library and public archive technicians",
    386: "52110 Film and video camera operators", 387: "52111 Graphic arts technicians",
    388: "52112 Broadcast technicians", 389: "52113 Audio and video recording technicians",
    390: "52114 Announcers and other broadcasters",
    391: "52119 Other motion pictures/broadcasting technical occupations",
    393: "52120 Graphic designers and illustrators", 394: "52121 Interior designers",
    398: "53100 Museum and art gallery occupations", 400: "53110 Photographers",
    401: "53111 Motion pictures and performing arts assistants",
    403: "53120 Dancers", 404: "53121 Actors and comedians",
    405: "53122 Painters, sculptors and visual artists",
    406: "53123 Theatre, fashion and creative designers",
    407: "53124 Artisans and craftspersons", 408: "53125 Patternmakers",
    411: "53200 Athletes", 412: "53201 Coaches", 413: "53202 Sports officials and referees",
    417: "54100 Program leaders in recreation, sport and fitness",
    421: "55109 Other performers",
    426: "60010 Corporate sales managers", 428: "60020 Retail and wholesale trade managers",
    430: "60030 Restaurant and food service managers", 431: "60031 Accommodation service managers",
    433: "60040 Managers in customer and personal services",
    437: "62010 Retail sales supervisors", 439: "62020 Food service supervisors",
    440: "62021 Executive housekeepers", 441: "62022 Accommodation and travel supervisors",
    442: "62023 Customer and information services supervisors",
    443: "62024 Cleaning supervisors", 444: "62029 Other services supervisors",
    447: "62100 Technical sales specialists - wholesale", 448: "62101 Retail and wholesale buyers",
    451: "62200 Chefs", 452: "62201 Funeral directors and embalmers",
    453: "62202 Jewellers and watch repairers",
    457: "63100 Insurance agents and brokers", 458: "63101 Real estate agents",
    459: "63102 Financial sales representatives",
    462: "63200 Cooks", 463: "63201 Butchers", 464: "63202 Bakers",
    466: "63210 Hairstylists and barbers", 467: "63211 Estheticians",
    469: "63220 Shoe repairers", 470: "63221 Upholsterers",
    474: "64100 Retail salespersons", 475: "64101 Sales and account representatives - wholesale",
    478: "64200 Tailors and dressmakers", 479: "64201 Image and personal consultants",
    482: "64300 Maîtres d'hôtel and hosts/hostesses", 483: "64301 Bartenders",
    485: "64310 Travel counsellors", 486: "64311 Pursers and flight attendants",
    487: "64312 Airline ticket and service agents",
    488: "64313 Transport ticket agents and cargo representatives",
    489: "64314 Hotel front desk clerks",
    491: "64320 Tour and travel guides", 492: "64321 Casino workers",
    493: "64322 Outdoor sport and recreational guides",
    496: "64400 Customer services reps - financial institutions",
    497: "64401 Postal services representatives",
    498: "64409 Other customer and information services representatives",
    500: "64410 Security guards",
    504: "65100 Cashiers", 505: "65101 Service station attendants",
    506: "65102 Store shelf stockers and order fillers", 507: "65109 Other sales occupations",
    510: "65200 Food and beverage servers",
    511: "65201 Food counter attendants and kitchen helpers",
    512: "65202 Meat cutters and fishmongers",
    514: "65210 Accommodation and travel support", 515: "65211 Amusement and recreation operators",
    517: "65220 Pet groomers and animal care workers", 518: "65229 Other personal services support",
    521: "65310 Light duty cleaners", 522: "65311 Specialized cleaners",
    523: "65312 Janitors and heavy-duty cleaners",
    525: "65320 Dry cleaning and laundry", 526: "65329 Other service support",
    531: "70010 Construction managers", 532: "70011 Home building and renovation managers",
    533: "70012 Facility operation and maintenance managers",
    535: "70020 Managers in transportation", 536: "70021 Postal and courier services managers",
    540: "72010 Supervisors, machining trades", 541: "72011 Supervisors, electrical trades",
    542: "72012 Supervisors, pipefitting trades", 543: "72013 Supervisors, carpentry trades",
    544: "72014 Supervisors, other construction trades",
    546: "72020 Supervisors, mechanic trades", 547: "72021 Supervisors, heavy equipment",
    548: "72022 Supervisors, printing", 549: "72023 Supervisors, railway transport",
    550: "72024 Supervisors, motor transport", 551: "72025 Supervisors, mail and message distribution",
    554: "72100 Machinists", 555: "72101 Tool and die makers", 556: "72102 Sheet metal workers",
    557: "72103 Boilermakers", 558: "72104 Structural metal fabricators", 559: "72105 Ironworkers",
    560: "72106 Welders", 563: "72200 Electricians", 564: "72201 Industrial electricians",
    565: "72202 Power system electricians", 566: "72203 Electrical power line workers",
    567: "72204 Telecommunications line installers", 568: "72205 Telecommunications equipment technicians",
    571: "72300 Plumbers", 572: "72301 Steamfitters and pipefitters", 573: "72302 Gas fitters",
    575: "72310 Carpenters", 576: "72311 Cabinetmakers",
    578: "72320 Bricklayers", 579: "72321 Insulators",
    582: "72400 Construction millwrights", 583: "72401 Heavy-duty equipment mechanics",
    584: "72402 HVAC mechanics", 585: "72403 Railway carmen",
    586: "72404 Aircraft mechanics", 587: "72405 Machine fitters",
    588: "72406 Elevator constructors and mechanics",
    590: "72410 Automotive service technicians", 591: "72411 Auto body technicians",
    593: "72420 Oil and solid fuel heating mechanics", 594: "72421 Appliance servicers",
    595: "72422 Electrical mechanics", 596: "72423 Motorcycle and ATV mechanics",
    597: "72429 Other small engine repairers",
    600: "72500 Crane operators", 601: "72501 Water well drillers",
    604: "72600 Air pilots and flight engineers", 605: "72601 Air traffic controllers",
    606: "72602 Deck officers, water transport", 607: "72603 Engineer officers, water transport",
    608: "72604 Railway traffic controllers", 611: "72999 Other technical trades",
    615: "73100 Concrete finishers", 616: "73101 Tilesetters",
    617: "73102 Plasterers and drywall installers", 619: "73110 Roofers and shinglers",
    620: "73111 Glaziers", 621: "73112 Painters and decorators",
    622: "73113 Floor covering installers",
    625: "73200 Residential and commercial installers", 626: "73201 General building maintenance workers",
    627: "73202 Pest controllers", 628: "73209 Other repairers and servicers",
    631: "73300 Transport truck drivers", 632: "73301 Bus drivers and transit operators",
    634: "73310 Railway locomotive engineers", 635: "73311 Railway conductors",
    638: "73400 Heavy equipment operators", 639: "73401 Printing press operators",
    640: "73402 Drillers and blasters",
    644: "74100 Mail and parcel sorters", 645: "74101 Letter carriers",
    646: "74102 Couriers and messengers",
    649: "74200 Railway yard and track maintenance", 650: "74201 Water transport crew",
    651: "74202 Air transport ramp attendants", 652: "74203 Automotive parts installers",
    653: "74204 Utility maintenance workers", 654: "74205 Public works equipment operators",
    658: "75100 Longshore workers", 659: "75101 Material handlers",
    661: "75110 Construction helpers and labourers", 662: "75119 Other trades helpers",
    665: "75200 Taxi and limousine drivers", 666: "75201 Delivery service drivers",
    668: "75210 Boat and cable ferry operators", 669: "75211 Railway and motor transport labourers",
    670: "75212 Public works labourers",
    675: "80010 Managers in natural resources and fishing", 677: "80020 Managers in agriculture",
    678: "80021 Managers in horticulture", 679: "80022 Managers in aquaculture",
    683: "82010 Supervisors, logging and forestry", 685: "82020 Supervisors, mining and quarrying",
    686: "82021 Supervisors, oil and gas drilling", 688: "82030 Agricultural service contractors",
    689: "82031 Supervisors, landscaping and grounds maintenance",
    693: "83100 Underground miners", 694: "83101 Oil and gas well drillers",
    696: "83110 Logging machinery operators", 698: "83120 Fishing masters", 699: "83121 Fishermen/women",
    703: "84100 Underground mine service workers", 704: "84101 Oil and gas drilling workers",
    706: "84110 Chain saw and skidder operators", 707: "84111 Silviculture and forestry workers",
    709: "84120 Specialized livestock workers", 710: "84121 Fishing vessel deckhands",
    714: "85100 Livestock labourers", 715: "85101 Harvesting labourers",
    716: "85102 Aquaculture and marine harvest labourers", 717: "85103 Nursery and greenhouse labourers",
    718: "85104 Trappers and hunters",
    720: "85110 Mine labourers", 721: "85111 Oil and gas drilling labourers",
    723: "85120 Logging and forestry labourers", 724: "85121 Landscaping labourers",
    729: "90010 Manufacturing managers", 730: "90011 Utilities managers",
    734: "92010 Supervisors, mineral and metal processing",
    735: "92011 Supervisors, petroleum and chemical processing",
    736: "92012 Supervisors, food and beverage processing",
    737: "92013 Supervisors, plastic and rubber manufacturing",
    738: "92014 Supervisors, forest products processing",
    739: "92015 Supervisors, textile and leather products",
    741: "92020 Supervisors, motor vehicle assembling",
    742: "92021 Supervisors, electronics manufacturing",
    743: "92022 Supervisors, furniture manufacturing",
    744: "92023 Supervisors, mechanical and metal products manufacturing",
    745: "92024 Supervisors, other products manufacturing",
    748: "92100 Power engineers and power systems operators",
    749: "92101 Water and waste treatment plant operators",
    753: "93100 Central control operators - mineral and metal processing",
    754: "93101 Central control operators - petroleum and chemical processing",
    755: "93102 Pulping and papermaking control operators",
    758: "93200 Aircraft assemblers and inspectors",
    762: "94100 Machine operators - mineral and metal", 763: "94101 Foundry workers",
    764: "94102 Glass forming machine operators", 765: "94103 Concrete and stone forming operators",
    766: "94104 Inspectors - mineral and metal processing",
    767: "94105 Metalworking and forging machine operators",
    768: "94106 Machining tool operators", 769: "94107 Other metal product machine operators",
    771: "94110 Chemical plant machine operators", 772: "94111 Plastics processing machine operators",
    773: "94112 Rubber processing machine operators",
    775: "94120 Sawmill machine operators", 776: "94121 Pulp mill machine operators",
    777: "94122 Paper converting machine operators", 778: "94123 Lumber graders",
    779: "94124 Woodworking machine operators", 780: "94129 Other wood processing operators",
    782: "94130 Textile fibre and yarn processing operators",
    783: "94131 Weavers and knitters", 784: "94132 Industrial sewing machine operators",
    785: "94133 Textile inspectors and graders",
    787: "94140 Food and beverage processing machine operators",
    788: "94141 Industrial butchers and meat cutters",
    789: "94142 Fish and seafood plant workers", 790: "94143 Food and beverage testers and graders",
    792: "94150 Plateless printing equipment operators",
    793: "94151 Camera and platemaking operators", 794: "94152 Binding and finishing operators",
    795: "94153 Photographic and film processors",
    798: "94200 Motor vehicle assemblers and inspectors",
    799: "94201 Electronics assemblers and inspectors",
    800: "94202 Electrical appliance assemblers", 801: "94203 Industrial electrical motor assemblers",
    802: "94204 Mechanical assemblers", 803: "94205 Electrical apparatus machine operators",
    805: "94210 Furniture assemblers and inspectors", 806: "94211 Other wood product assemblers",
    807: "94212 Plastic products assemblers", 808: "94213 Industrial painters and coaters",
    809: "94219 Other product assemblers",
    813: "95100 Labourers in mineral and metal processing", 814: "95101 Labourers in metal fabrication",
    815: "95102 Labourers in chemical processing", 816: "95103 Labourers in wood and pulp processing",
    817: "95104 Labourers in rubber and plastic manufacturing",
    818: "95105 Labourers in textile processing", 819: "95106 Labourers in food processing",
    820: "95107 Labourers in fish processing", 821: "95109 Other labourers in manufacturing",
}

# Education dimension IDs in table 98100403 (same 16 members as labour_force)
NOC_DIST_EDU = LABOUR_FORCE_EDU

# ── Table 98100412: Income by NOC and CIP ──
# Dims: Geo(14), Gender(3), Age(15), Education(16), CIP(500), WorkActivity(5), NOC(821), IncomeStats(7)
# Coordinates: {geo}.{gender}.{age}.{edu}.{cip}.{work_activity}.{noc}.{income_stat}.0.0
# Age IDs: 1=Total, 2=15-24, 3=25-64
# WorkActivity: 1=Total, 4=Full-year-full-time
# IncomeStats: 3=Median employment income, 4=Average employment income
# NOC member IDs are the same as tables 98100403 (shared 821-member NOC 2021 dimension)
# CIP member IDs are the same as tables 98100403/98100409 (shared 500-member CIP 2021 dimension)

NOC_INCOME_AGE = {
    "Total": 1,
    "15-24": 2,
    "25-64": 3,
}

NOC_INCOME_WORK_ACTIVITY = {
    "Total": 1,
    "Full-year-full-time": 4,
}

NOC_INCOME_STATS = {
    "Median employment income": 3,
    "Average employment income": 4,
}
