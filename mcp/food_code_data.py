"""
Built-in FDA Food Code classification table.
Covers the main section prefixes (e.g. "3-501") used in Montana health inspections.
Risk levels: Priority (P), Priority Foundation (Pf), Core (C)
"""

# Keyed by section prefix string (e.g. "3-501").
# Each entry: category, chapter, risk_level, description
SECTIONS = {
    # ── Chapter 2: Management and Personnel ────────────────────────────────
    "2-102": {
        "category": "Knowledge & Responsibilities",
        "chapter": "Management and Personnel",
        "risk_level": "Priority Foundation",
        "description": "Person in charge must demonstrate food safety knowledge and ensure employees follow food code requirements.",
    },
    "2-103": {
        "category": "Person in Charge – Duties",
        "chapter": "Management and Personnel",
        "risk_level": "Priority Foundation",
        "description": "Person in charge is responsible for ensuring compliance with this Code by food employees.",
    },
    "2-201": {
        "category": "Employee Health – Reporting",
        "chapter": "Management and Personnel",
        "risk_level": "Priority",
        "description": "Food employees must report illnesses, symptoms, and diagnoses that can be transmitted through food.",
    },
    "2-301": {
        "category": "Handwashing – When & How",
        "chapter": "Management and Personnel",
        "risk_level": "Priority",
        "description": "Food employees must clean their hands and exposed portions of arms using the required handwashing procedure.",
    },
    "2-302": {
        "category": "Fingernails",
        "chapter": "Management and Personnel",
        "risk_level": "Priority Foundation",
        "description": "Food employees must keep their fingernails trimmed, filed, and maintained so that nail edges are clean.",
    },
    "2-303": {
        "category": "Jewelry",
        "chapter": "Management and Personnel",
        "risk_level": "Core",
        "description": "Food employees may not wear jewelry (including medical information jewelry) on their arms and hands while preparing food.",
    },
    "2-304": {
        "category": "Outer Clothing",
        "chapter": "Management and Personnel",
        "risk_level": "Core",
        "description": "Food employees must wear clean outer clothing to prevent contamination of food.",
    },
    "2-401": {
        "category": "Eating, Drinking, Tobacco",
        "chapter": "Management and Personnel",
        "risk_level": "Priority",
        "description": "Food employees may not eat, drink, or use tobacco in ways that may contaminate food or food-contact surfaces.",
    },
    "2-402": {
        "category": "Hair Restraints",
        "chapter": "Management and Personnel",
        "risk_level": "Core",
        "description": "Food employees must wear hair restraints (hat, hair covering, or net) to prevent contamination of food.",
    },

    # ── Chapter 3: Food ─────────────────────────────────────────────────────
    "3-101": {
        "category": "Condition – Safe, Unadulterated, Honestly Presented",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Food must be safe, unadulterated, and honestly presented.",
    },
    "3-201": {
        "category": "Sources – Approved",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Food must be obtained from approved sources – inspected and regulated facilities.",
    },
    "3-202": {
        "category": "Condition on Receipt",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Food must be received in good condition, safe, unadulterated, and at proper temperatures.",
    },
    "3-203": {
        "category": "Shellstock Identification",
        "chapter": "Food",
        "risk_level": "Priority Foundation",
        "description": "Shellstock must have original container tags maintained for traceability.",
    },
    "3-301": {
        "category": "Preventing Contamination – Bare Hands",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Food employees may not contact exposed, ready-to-eat food with their bare hands.",
    },
    "3-302": {
        "category": "Food Protection – Cross-Contamination",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Food must be protected from cross-contamination by separating raw animal foods from ready-to-eat foods.",
    },
    "3-303": {
        "category": "Food Protection – Ice",
        "chapter": "Food",
        "risk_level": "Core",
        "description": "Ice used to cool food or equipment may not be used as food for human consumption.",
    },
    "3-304": {
        "category": "Food Protection – Equipment, Utensils, Linens",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Food must be protected from contamination by equipment, utensils, linens, and single-service articles.",
    },
    "3-305": {
        "category": "Food Protection – Premises",
        "chapter": "Food",
        "risk_level": "Core",
        "description": "Food must be protected from contamination by storing it in a clean, dry location away from splash, dust, and other contamination.",
    },
    "3-306": {
        "category": "Consumer Self-Service",
        "chapter": "Food",
        "risk_level": "Priority Foundation",
        "description": "Raw, unpackaged animal food may not be offered for consumer self-service.",
    },
    "3-401": {
        "category": "Cooking Temperatures",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Raw animal foods must be cooked to the specified minimum internal temperatures to destroy pathogens.",
    },
    "3-402": {
        "category": "Freezing for Parasite Destruction",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Fish that is served raw or undercooked must be frozen to destroy parasites.",
    },
    "3-403": {
        "category": "Reheating",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Cooked and cooled food that is reheated for hot holding must reach 165°F within 2 hours.",
    },
    "3-501": {
        "category": "Temperature and Time Control for Safety Food (TCS)",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "TCS food must be maintained at 41°F (5°C) or below for cold holding, or 135°F (57°C) or above for hot holding.",
    },
    "3-502": {
        "category": "Specialized Processing Methods",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "Specialized food processing methods (e.g., ROP, curing, smoking) require an approved HACCP plan.",
    },
    "3-601": {
        "category": "Food Identity – Labeling",
        "chapter": "Food",
        "risk_level": "Core",
        "description": "Food on display must be labeled and not misrepresented.",
    },
    "3-602": {
        "category": "Labeling – Packaged Food",
        "chapter": "Food",
        "risk_level": "Core",
        "description": "Food packaged in a food establishment must be labeled as specified.",
    },
    "3-701": {
        "category": "Discarding Unsafe, Adulterated Food",
        "chapter": "Food",
        "risk_level": "Priority",
        "description": "A food that is unsafe or adulterated must be discarded or reconditioned.",
    },

    # ── Chapter 4: Equipment, Utensils, and Linens ─────────────────────────
    "4-101": {
        "category": "Equipment Materials – Safe & Durable",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority Foundation",
        "description": "Materials used in the construction of equipment must be safe, durable, corrosion-resistant, and nonabsorbent.",
    },
    "4-201": {
        "category": "Equipment Design – Durability",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority Foundation",
        "description": "Equipment must be designed and constructed to be durable and capable of withstanding normal use.",
    },
    "4-301": {
        "category": "Equipment Capacity",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority Foundation",
        "description": "Equipment must be sufficient in number and capacity to provide food temperature control.",
    },
    "4-501": {
        "category": "Equipment Maintenance & Calibration",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority Foundation",
        "description": "Equipment must be maintained in a state of repair and condition consistent with the Food Code. Temperature measuring devices must be calibrated.",
    },
    "4-601": {
        "category": "Cleaning Equipment – Food-Contact Surfaces",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority Foundation",
        "description": "Equipment food-contact surfaces and utensils must be clean to sight and touch.",
    },
    "4-602": {
        "category": "Cleaning Frequency",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority",
        "description": "Equipment food-contact surfaces and utensils must be cleaned and sanitized at required frequencies.",
    },
    "4-701": {
        "category": "Sanitization – Required",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority",
        "description": "Utensils and food-contact surfaces of equipment must be sanitized before use and after cleaning.",
    },
    "4-702": {
        "category": "Sanitization – Before Use After Cleaning",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority",
        "description": "Utensils and food-contact surfaces must be sanitized before use after each cleaning cycle.",
    },
    "4-703": {
        "category": "Sanitization Methods – Hot Water & Chemical",
        "chapter": "Equipment, Utensils, and Linens",
        "risk_level": "Priority",
        "description": "Sanitization must be accomplished by hot water or chemical sanitizer at specified concentrations and contact times.",
    },

    # ── Chapter 5: Water, Plumbing, and Waste ──────────────────────────────
    "5-101": {
        "category": "Water Source – Approved",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Priority",
        "description": "Water must come from an approved source – a public water system or a non-community water system approved by the regulatory authority.",
    },
    "5-102": {
        "category": "Water Quality",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Priority",
        "description": "Water must meet EPA drinking water quality standards.",
    },
    "5-201": {
        "category": "Plumbing – Approved System",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Priority",
        "description": "A plumbing system must be designed, installed, and maintained according to applicable plumbing codes.",
    },
    "5-202": {
        "category": "Plumbing – Design & Construction",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Priority Foundation",
        "description": "Plumbing system and hoses must be properly designed and maintained to prevent backflow and contamination.",
    },
    "5-401": {
        "category": "Sewage Disposal",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Priority",
        "description": "Sewage must be disposed of through an approved sewage disposal system.",
    },
    "5-402": {
        "category": "Backflow Prevention",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Priority",
        "description": "A direct connection may not exist between the sewage system and a drain originating from equipment in which food is handled.",
    },
    "5-501": {
        "category": "Refuse Receptacles",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Core",
        "description": "Indoor and outdoor garbage and refuse containers must be sufficient in number and adequate to contain refuse.",
    },
    "5-502": {
        "category": "Refuse Removal",
        "chapter": "Water, Plumbing, and Waste",
        "risk_level": "Core",
        "description": "Refuse, recyclables, and returnables must be removed from the premises at a frequency to minimize odors and the attraction of insects and rodents.",
    },

    # ── Chapter 6: Physical Facilities ─────────────────────────────────────
    "6-101": {
        "category": "Indoor Areas – Floor, Wall, Ceiling Materials",
        "chapter": "Physical Facilities",
        "risk_level": "Core",
        "description": "Indoor floor, wall, and ceiling surfaces must be smooth, durable, and easily cleanable in food preparation areas.",
    },
    "6-201": {
        "category": "Cleanability – Floors, Walls, Ceilings",
        "chapter": "Physical Facilities",
        "risk_level": "Core",
        "description": "Floors, walls, and ceilings must be designed, constructed, and installed to be smooth, easily cleanable, and nonabsorbent.",
    },
    "6-301": {
        "category": "Handwashing Facilities – Availability",
        "chapter": "Physical Facilities",
        "risk_level": "Priority Foundation",
        "description": "Handwashing sinks must be available in food preparation, food dispensing, warewashing, and toilet areas.",
    },
    "6-302": {
        "category": "Handwashing Facilities – Supplies",
        "chapter": "Physical Facilities",
        "risk_level": "Priority Foundation",
        "description": "Each handwashing sink must be provided with hand-cleaner and individual disposable towels or a hand-drying device.",
    },
    "6-303": {
        "category": "Lighting",
        "chapter": "Physical Facilities",
        "risk_level": "Core",
        "description": "Light intensity must meet the specified minimums in food preparation, storage, and toilet areas.",
    },
    "6-304": {
        "category": "Ventilation",
        "chapter": "Physical Facilities",
        "risk_level": "Core",
        "description": "Ventilation hood systems must be designed and operated to prevent grease or condensation from dripping onto food or food-contact surfaces.",
    },
    "6-501": {
        "category": "Facility Maintenance – Pest Control",
        "chapter": "Physical Facilities",
        "risk_level": "Core",
        "description": "The physical facilities must be maintained in good repair and cleaned as often as necessary to keep them clean. Effective pest control measures must be used.",
    },

    # ── Chapter 7: Poisonous or Toxic Materials ─────────────────────────────
    "7-101": {
        "category": "Poisonous/Toxic – Original Containers",
        "chapter": "Poisonous or Toxic Materials",
        "risk_level": "Priority Foundation",
        "description": "Poisonous or toxic materials must be stored in their original containers or properly labeled working containers.",
    },
    "7-102": {
        "category": "Poisonous/Toxic – Working Containers",
        "chapter": "Poisonous or Toxic Materials",
        "risk_level": "Priority Foundation",
        "description": "Working containers used for storing poisonous or toxic materials must be clearly and individually identified.",
    },
    "7-201": {
        "category": "Poisonous/Toxic – Storage",
        "chapter": "Poisonous or Toxic Materials",
        "risk_level": "Priority",
        "description": "Poisonous or toxic materials must be stored so they cannot contaminate food, equipment, utensils, linens, and single-service articles.",
    },
    "7-202": {
        "category": "Conditions of Use",
        "chapter": "Poisonous or Toxic Materials",
        "risk_level": "Priority",
        "description": "Only those poisonous or toxic materials necessary to maintain the establishment, equipment, and for use in food preparation may be present.",
    },
    "7-203": {
        "category": "Restricted Use Pesticides",
        "chapter": "Poisonous or Toxic Materials",
        "risk_level": "Priority",
        "description": "Restricted use pesticides must be applied only by a certified applicator or person under a certified applicator's direct supervision.",
    },
    "7-204": {
        "category": "Sanitizers – Criteria",
        "chapter": "Poisonous or Toxic Materials",
        "risk_level": "Priority",
        "description": "Chemical sanitizers and other chemical antimicrobial agents must meet EPA registration requirements.",
    },
    "7-207": {
        "category": "Personal Care Items",
        "chapter": "Poisonous or Toxic Materials",
        "risk_level": "Priority Foundation",
        "description": "Employees' personal care items must be stored in a way that prevents contamination of food and food-contact surfaces.",
    },
}

# Chapter-level fallback when a section prefix isn't in the table above
CHAPTERS = {
    "1": {"chapter": "Purpose and Definitions", "risk_level": "Core"},
    "2": {"chapter": "Management and Personnel", "risk_level": "Priority Foundation"},
    "3": {"chapter": "Food", "risk_level": "Priority"},
    "4": {"chapter": "Equipment, Utensils, and Linens", "risk_level": "Priority Foundation"},
    "5": {"chapter": "Water, Plumbing, and Waste", "risk_level": "Priority Foundation"},
    "6": {"chapter": "Physical Facilities", "risk_level": "Core"},
    "7": {"chapter": "Poisonous or Toxic Materials", "risk_level": "Priority"},
}

RISK_LEVEL_DESCRIPTIONS = {
    "Priority": (
        "PRIORITY — Directly linked to foodborne illness or injury. "
        "These violations must be corrected immediately or require the food establishment to voluntarily close."
    ),
    "Priority Foundation": (
        "PRIORITY FOUNDATION — Supports Priority items (training, procedures, equipment, documentation). "
        "Failure to control these leads to Priority violations."
    ),
    "Core": (
        "CORE — Good retail practice. Not directly linked to illness, "
        "but violations are tracked and must be corrected within a reasonable timeframe."
    ),
}


def lookup_section(code: str) -> dict | None:
    """Return classification for a violation code like '3-501.16' or '3-501'."""
    code = code.strip()
    # Try to match the section prefix (e.g. "3-501" from "3-501.16")
    parts = code.split(".")
    prefix = parts[0]  # e.g. "3-501"
    if prefix in SECTIONS:
        return {**SECTIONS[prefix], "matched_prefix": prefix}
    # Fall back to chapter-level match
    chapter_num = prefix.split("-")[0] if "-" in prefix else prefix[0]
    if chapter_num in CHAPTERS:
        ch = CHAPTERS[chapter_num]
        return {
            "category": f"Chapter {chapter_num} violation",
            "chapter": ch["chapter"],
            "risk_level": ch["risk_level"],
            "description": f"Violation falls under FDA Food Code Chapter {chapter_num}: {ch['chapter']}.",
            "matched_prefix": f"chapter {chapter_num}",
        }
    return None
