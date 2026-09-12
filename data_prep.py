import json
import copy
import numpy as np

# ============================================================
# DATASET
# ============================================================

DATA_PATH = "data/NYC_CORRIDORS.full.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

corridors = data["corridors"]

corridor_lookup = {
    corridor["corridor_id"]: corridor
    for corridor in corridors
}


# ============================================================
# CORRIDOR LIST
# Compatible with app.py:
# app.py expects a list of dictionaries containing
# corridor_id, name and borough.
# ============================================================

def corridor_list():
    return [
        (c["corridor_id"], c["name"])
        for c in corridors
    ]


# ============================================================
# CORRIDOR DNA
# Compatible with app.py and llm_engine.py
# ============================================================

def corridor_dna(corridor):
    magnets = corridor.get("demand_magnets", {})

    # app.py displays these as decimal values with 2 places.
    food_demand = magnets.get("restaurant_district", 0)
    retail_demand = magnets.get("retail", 0)

    scores = corridor.get("audience_scores", {})
    top_audiences = [
        x[0]
        for x in sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
    ]

    anchors = corridor.get("anchors", [])
    anchor_name = "None"
    if anchors:
        anchor_name = anchors[0].get("name", "None")

    return {
        "name": corridor.get("name", ""),
        "borough": corridor.get("borough", ""),
        "top_audiences": top_audiences,
        "food_demand": food_demand,
        "retail_demand": retail_demand,
        "anchor": anchor_name,
        "character": corridor.get("character", "")
    }


# ============================================================
# HEALTH SCORE
# ============================================================

def health_score(corridor):
    audience_values = np.array(
        list(corridor.get("audience_scores", {}).values()),
        dtype=float
    )

    if len(audience_values) == 0:
        audience_score = 0
    else:
        # Keep Member 1's original scoring idea.
        audience_score = (
            float(np.mean(audience_values)) * 10
        )

    business_score = (
        corridor.get("magnet_diversity", 0) or 0
    ) * 100

    anchor = corridor.get("anchor_concentration") or {}

    effective_anchor_count = anchor.get(
        "effective_anchor_count", 0
    )

    anchor_score = min(
        float(effective_anchor_count) * 10,
        100
    )

    dayparts = (
        corridor.get("behavior", {})
        .get("daypart_occasion_density", {})
    )

    if dayparts:
        activity_score = (
            sum(dayparts.values()) / len(dayparts)
        )
    else:
        activity_score = 0

    final_score = (
        audience_score * 0.30
        + business_score * 0.25
        + anchor_score * 0.25
        + activity_score * 0.20
    )

    final_score = max(0, min(100, final_score))

    sub_scores = {
        "audience_score": round(max(0, min(100, audience_score))),
        "business_score": round(max(0, min(100, business_score))),
        "anchor_score": round(max(0, min(100, anchor_score))),
        "activity_score": round(max(0, min(100, activity_score))),
    }

    return round(final_score), sub_scores


# ============================================================
# HEALTH STATUS
# IMPORTANT:
# app.py STATUS_COLOR uses exactly:
# Critical / Weak / Moderate / Strong
# ============================================================

def health_status(score):
    if score <= 40:
        return "Critical"
    elif score <= 60:
        return "Weak"
    elif score <= 80:
        return "Moderate"
    else:
        return "Strong"


# ============================================================
# DIAGNOSIS FACTS
# Compatible with llm_engine.diagnosis_report()
# ============================================================

def diagnosis_facts(corridor, score):
    facts = []

    audience_scores = corridor.get("audience_scores", {})

    if audience_scores:
        top_audience = max(
            audience_scores,
            key=audience_scores.get
        )

        if audience_scores[top_audience] >= 7:
            facts.append(
                f"overdependence on {top_audience.replace('_', ' ')}"
            )

    dayparts = (
        corridor.get("behavior", {})
        .get("daypart_occasion_density", {})
    )

    if dayparts.get("weekday_am", 100) < 45:
        facts.append("weak weekday morning activity")

    if dayparts.get("late_night", 100) < 30:
        facts.append("minimal late-night activity")

    business_score = (
        corridor.get("magnet_diversity", 0) or 0
    ) * 100

    if business_score < 50:
        facts.append("low business/magnet diversity")

    anchor = corridor.get("anchor_concentration") or {}

    if anchor.get("effective_anchor_count", 0) < 3:
        facts.append("thin anchor base")

    if not facts:
        facts.append(
            "no major weaknesses detected — corridor is well balanced"
        )

    return facts


# ============================================================
# PRESCRIPTIONS
#
# app.py expects each prescription to be a dictionary with:
#   prescription["name"]
#   prescription["score"]
#
# llm_engine.prescription_reasons() expects the same structure.
# ============================================================

def prescriptions(corridor, n=3):
    # Prefer the dataset's own pre-scored archetype matches if present.
    matches = corridor.get("cafe_archetype_matches", [])

    if matches:
        eligible = [
            m for m in matches
            if m.get("host_context_present", True) is not False
        ]

        ranked = sorted(
            eligible,
            key=lambda m: m.get("score", 0),
            reverse=True
        )

        result = []

        for m in ranked[:n]:
            name = (
                m.get("name")
                or m.get("archetype")
                or m.get("label")
                or "Recommended Concept"
            )

            result.append({
                "name": name,
                "score": float(m.get("score", 0))
            })

        if result:
            return result

    # Fallback for datasets where cafe_archetype_matches is absent.
    magnets = corridor.get("demand_magnets", {})

    scores = {
        "Add University": magnets.get("education", 0),
        "Add Hospital": magnets.get("medical", 0),
        "Add Coworking Space": magnets.get("office", 0),
        "Add Mall": magnets.get("retail", 0),
        "Add Gym": magnets.get("grocery_routine", 0),
    }

    ranked = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        {
            "name": name,
            "score": float(score)
        }
        for name, score in ranked[:n]
    ]


# ============================================================
# PROFILE API
# This is the main function used by app.py.
# ============================================================

def get_corridor_profile(corridor_id):
    if corridor_id not in corridor_lookup:
        raise KeyError(f"Unknown corridor_id: {corridor_id}")

    corridor = corridor_lookup[corridor_id]

    dna = corridor_dna(corridor)
    score, sub_scores = health_score(corridor)
    status = health_status(score)

    return {
        "corridor": corridor,
        "health_score": score,
        "status": status,
        "sub_scores": sub_scores,
        "diagnosis_facts": diagnosis_facts(
            corridor,
            score
        ),
        "prescriptions": prescriptions(corridor),
        "dna": dna
    }


# ============================================================
# IMPACT SIMULATOR
#
# IMPORTANT:
# app.py does:
#     list(data_prep.INTERVENTIONS.keys())
# Therefore INTERVENTIONS MUST be a dictionary, not a list.
# ============================================================

INTERVENTIONS = {
    "Add Hospital": {
        "demand_sources": {
            "medical_context": 0.25
        },
        "demand_magnets": {
            "medical": 0.20
        },
        "audience": {
            "family_household": 3,
            "hospital_workers": 3
        },
        "daypart": {
            "weekday_am": 20
        },
        "anchor_boost": True
    },

    "Add University": {
        "demand_sources": {
            "university_context": 0.30
        },
        "demand_magnets": {
            "education": 0.20
        },
        "audience": {
            "faculty_staff": 3,
            "hybrid_remote": 2
        },
        "daypart": {
            "weekday_am": 15,
            "weekday_midday": 15
        },
        "anchor_boost": True
    },

    "Add Coworking Space": {
        "demand_magnets": {
            "office": 0.18
        },
        "audience": {
            "hybrid_remote": 4,
            "office_routine": 3
        },
        "daypart": {
            "weekday_am": 25,
            "weekday_midday": 20
        },
        "anchor_boost": False
    },

    "Add Mall": {
        "demand_magnets": {
            "retail": 0.25,
            "retail_destination": 0.15
        },
        "audience": {
            "everyday_shoppers": 4
        },
        "daypart": {
            "weekend_day": 25
        },
        "anchor_boost": True
    },

    "Add Gym": {
        "demand_magnets": {
            "grocery_routine": 0.05
        },
        "audience": {
            "fitness_active": 4
        },
        "daypart": {
            "weekday_am": 12,
            "weekday_evening": 10
        },
        "anchor_boost": False
    }
}


def apply_intervention(corridor, intervention_name):
    """Return a modified COPY of the corridor."""
    if intervention_name not in INTERVENTIONS:
        raise KeyError(
            f"Unknown intervention: {intervention_name}"
        )

    new_c = copy.deepcopy(corridor)
    effect = INTERVENTIONS[intervention_name]

    # Demand sources
    for key, delta in effect.get(
        "demand_sources", {}
    ).items():
        if "demand_sources" not in new_c:
            new_c["demand_sources"] = {}

        new_c["demand_sources"][key] = min(
            1.0,
            new_c["demand_sources"].get(key, 0) + delta
        )

    # Demand magnets
    for key, delta in effect.get(
        "demand_magnets", {}
    ).items():
        if "demand_magnets" not in new_c:
            new_c["demand_magnets"] = {}

        new_c["demand_magnets"][key] = min(
            1.0,
            new_c["demand_magnets"].get(key, 0) + delta
        )

    # Audience scores
    for key, delta in effect.get(
        "audience", {}
    ).items():
        if "audience_scores" not in new_c:
            new_c["audience_scores"] = {}

        new_c["audience_scores"][key] = min(
            10,
            new_c["audience_scores"].get(key, 0) + delta
        )

    # Dayparts
    for key, delta in effect.get(
        "daypart", {}
    ).items():
        if "behavior" not in new_c:
            new_c["behavior"] = {}

        if "daypart_occasion_density" not in new_c["behavior"]:
            new_c["behavior"]["daypart_occasion_density"] = {}

        dp = new_c["behavior"]["daypart_occasion_density"]

        dp[key] = min(
            100,
            dp.get(key, 0) + delta
        )

    # Keep dataset-level diversity moving slightly in the
    # positive direction after adding a new magnet.
    current_diversity = (
        new_c.get("magnet_diversity", 0) or 0
    )

    new_c["magnet_diversity"] = min(
        1.0,
        current_diversity + 0.03
    )

    # Physical anchors such as hospitals, universities and
    # malls increase the effective anchor count.
    if (
        effect.get("anchor_boost")
        and new_c.get("anchor_concentration")
    ):
        ac = new_c["anchor_concentration"]

        ac["effective_anchor_count"] = (
            ac.get("effective_anchor_count", 0) + 1
        )

        ac["hhi"] = max(
            0.03,
            ac.get("hhi", 0.1) * 0.85
        )

    return new_c


def simulate_impact(corridor_id, intervention_name):
    """Return exactly the fields expected by app.py and llm_engine.py."""

    corridor = corridor_lookup[corridor_id]

    before_score, before_sub = health_score(corridor)

    modified = apply_intervention(
        corridor,
        intervention_name
    )

    after_score, after_sub = health_score(modified)

    return {
        "intervention": intervention_name,
        "before_score": before_score,
        "after_score": after_score,
        "before_sub": before_sub,
        "after_sub": after_sub,
        "delta": after_score - before_score
    }


# ============================================================
# OPTIONAL COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":
    first_id = corridors[0]["corridor_id"]

    profile = get_corridor_profile(first_id)

    print("\n===== CORRIDOR RX REPORT =====")
    print("Name:", profile["dna"]["name"])
    print("Borough:", profile["dna"]["borough"])
    print("Top Audiences:", profile["dna"]["top_audiences"])
    print("Food Demand:", profile["dna"]["food_demand"])
    print("Retail Demand:", profile["dna"]["retail_demand"])
    print("Anchor:", profile["dna"]["anchor"])
    print("Health Score:", profile["health_score"])
    print("Status:", profile["status"])
    print("Sub Scores:", profile["sub_scores"])
    print("Diagnosis Facts:", profile["diagnosis_facts"])
    print("Prescriptions:", profile["prescriptions"])
