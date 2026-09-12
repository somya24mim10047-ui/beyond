import google.generativeai as genai

# ============================================================
# SETUP
# ============================================================
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))   # <-- put your real key here
model = genai.GenerativeModel("gemini-flash-lite-latest")


# ============================================================
# INTERNAL HELPER — not part of the contract, just used by the 4 functions below
# ============================================================
def _ask_gemini(system_instruction, user_content):
    full_prompt = f"{system_instruction}\n\n{user_content}"
    response = model.generate_content(full_prompt)
    return response.text


# ============================================================
# 1. diagnosis_report(facts, character) -> str
# ============================================================
def diagnosis_report(facts: list, character: str) -> str:
    system_instruction = (
        "You are a corridor health doctor writing a short diagnosis report for a commercial "
        "district. Speak like a doctor giving a clear, professional diagnosis — confident, "
        "concise, no fluff. Do NOT invent any new problems beyond what is listed as facts. "
        "If no facts are provided, state clearly that the corridor shows no major issues "
        "and briefly note its strengths instead."
    )
    facts_text = "\n".join(f"- {f}" for f in facts) if facts else "(none — no issues detected)"
    user_content = f"""
Corridor description: {character}

Detected issues (facts):
{facts_text}

Write a short diagnosis report (3-5 sentences) in the style of a doctor's diagnosis.
Reference the corridor's character where relevant.
"""
    return _ask_gemini(system_instruction, user_content)


# ============================================================
# 2. prescription_reasons(prescription, dna) -> str
# ============================================================
def prescription_reasons(prescription: dict, dna: dict) -> str:
    system_instruction = (
        "You are a corridor business advisor. Given ONE recommended business (already scored "
        "by a matching model) and the corridor's profile ('DNA'), write a short 'Why Recommended?' "
        "explanation using confident bullet points starting with a checkmark (✓). "
        "Do NOT invent facts beyond what is given in the business info and corridor DNA."
    )
    user_content = f"""
Recommended business: {prescription.get('name')} (match score: {prescription.get('score')})

Corridor DNA:
- Top audiences: {dna.get('top_audiences')}
- Food demand: {dna.get('food_demand')}
- Retail demand: {dna.get('retail_demand')}
- Anchor: {dna.get('anchor')}
- Character: {dna.get('character')}

Write:
Reason:
✓ (bullet point tying the business to the DNA above)
✓ (another bullet point)
"""
    return _ask_gemini(system_instruction, user_content)


# ============================================================
# 3. impact_narrative(sim_result, character) -> str
# ============================================================
def impact_narrative(sim_result: dict, character: str) -> str:
    system_instruction = (
        "You are a corridor impact analyst. Given a before/after health score and sub-scores "
        "from a simulated intervention, explain WHY the score changed in 2-3 confident sentences. "
        "Be specific about which factors likely drove the change. "
        "Do NOT invent numbers beyond what is given."
    )
    user_content = f"""
Corridor description: {character}

Intervention applied: {sim_result.get('intervention')}

Health Score: {sim_result.get('before_score')} -> {sim_result.get('after_score')} (delta: {sim_result.get('delta')})

Sub-scores before: {sim_result.get('before_sub')}
Sub-scores after: {sim_result.get('after_sub')}

Explain why the health score changed as it did, referencing the specific sub-scores that improved.
"""
    return _ask_gemini(system_instruction, user_content)


# ============================================================
# 4. ask_the_corridor(profile, question) -> str
# ============================================================
def ask_the_corridor(profile: dict, question: str) -> str:
    system_instruction = (
        "You are 'Ask the Corridor' — an AI assistant that answers questions about ONE specific "
        "commercial corridor using ONLY the profile data provided below. Be direct and "
        "conversational, like a knowledgeable local analyst. If the data doesn't contain the "
        "answer, say so honestly instead of guessing or making up a number."
    )
    user_content = f"""
Corridor profile:
{profile}

User question: {question}

Answer the question using only the corridor profile above.
"""
    return _ask_gemini(system_instruction, user_content)


# ============================================================
# TESTS — only run when this file is executed directly.
# Safe to leave in when sharing: these do NOT run when Member 3's
# app.py imports this file with `import llm_engine`.
# ============================================================
if __name__ == "__main__":

    print("--- diagnosis_report test ---")
    print(diagnosis_report(
        ["overdependence on students", "weak weekday morning activity"],
        "A lively corridor near a major university, popular with students in the evenings."
    ))
    print()

    print("--- diagnosis_report edge case (healthy corridor) ---")
    print(diagnosis_report([], "A balanced, thriving corridor with strong foot traffic all day."))
    print()

    print("--- prescription_reasons test ---")
    fake_prescription = {"name": "Residential amenity cafe", "score": 0.80}
    fake_dna = {
        "top_audiences": ["community_social", "evening_commuters", "family_household"],
        "food_demand": 0.25,
        "retail_demand": 0.29,
        "anchor": "Empire Outlets–St. George Terminal",
        "character": "A quiet residential corridor near a transit terminal."
    }
    print(prescription_reasons(fake_prescription, fake_dna))
    print()

    print("--- impact_narrative test ---")
    fake_sim_result = {
        "intervention": "Add University",
        "before_score": 68,
        "after_score": 84,
        "before_sub": {"audience_diversity": 40, "activity_balance": 30, "business_diversity": 20, "anchor_strength": 80},
        "after_sub": {"audience_diversity": 45, "activity_balance": 50, "business_diversity": 32, "anchor_strength": 90},
        "delta": 16
    }
    print(impact_narrative(fake_sim_result, "A quiet residential corridor near a transit terminal."))
    print()

    print("--- ask_the_corridor test ---")
    fake_profile = {
        "corridor": {"name": "University Row"},
        "health_score": 68,
        "status": "Moderate",
        "sub_scores": {"audience_diversity": 40, "activity_balance": 30, "business_diversity": 20, "anchor_strength": 80},
    }
    print(ask_the_corridor(fake_profile, "Why is this corridor weak in the mornings?"))