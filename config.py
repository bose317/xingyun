"""Configuration: API endpoints, table IDs, dimension mappings."""

API_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest/"

# Table keys → 8-digit Product IDs
TABLES = {
    "labour_force": 98100445,
    "income": 98100409,
    "unemployment_trends": 14100020,
    "job_vacancies": 14100443,
    "graduate_outcomes": 37100283,
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
