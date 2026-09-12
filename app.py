"""
CorridorRx — app.py  (Member 3's file: Frontend/App Engineer)

This file owns navigation and layout only. All numbers come from data_prep.py,
all narrative text comes from llm_engine.py. Don't compute anything here.

Run with:  streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go

import data_prep
import llm_engine

st.set_page_config(page_title="CorridorRx", page_icon="🩺", layout="centered")

PAGES = [
    "1. Select Corridor",
    "2. Health Dashboard",
    "3. Diagnosis Report",
    "4. Prescription",
    "5. Impact Simulator",
    "6. Impact Results",
    "Ask the Corridor",
]

STATUS_COLOR = {
    "Critical": "#C0392B",
    "Weak": "#E67E22",
    "Moderate": "#D4AC0D",
    "Strong": "#27AE60",
}


def init_state():
    if "corridor_id" not in st.session_state:
        st.session_state.corridor_id = None
    if "sim_result" not in st.session_state:
        st.session_state.sim_result = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def require_corridor():
    if not st.session_state.corridor_id:
        st.warning("Select a corridor first (Page 1).")
        st.stop()


def gauge_chart(score, status):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": " / 100"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": STATUS_COLOR[status]},
                "steps": [
                    {"range": [0, 40], "color": "#F5D6D2"},
                    {"range": [40, 60], "color": "#FBE3CC"},
                    {"range": [60, 80], "color": "#FBF0C4"},
                    {"range": [80, 100], "color": "#D5EDD9"},
                ],
            },
            title={"text": status},
        )
    )
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=10))
    return fig


def radar_chart(sub_scores):
    labels = list(sub_scores.keys())
    values = list(sub_scores.values())
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill="toself")
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=350,
        margin=dict(l=30, r=30, t=30, b=30),
    )
    return fig


def before_after_bar(before_sub, after_sub):
    labels = list(before_sub.keys())
    fig = go.Figure(
        data=[
            go.Bar(name="Before", x=labels, y=[before_sub[k] for k in labels]),
            go.Bar(name="After", x=labels, y=[after_sub[k] for k in labels]),
        ]
    )
    fig.update_layout(barmode="group", height=350, margin=dict(l=20, r=20, t=30, b=20))
    return fig


def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Source Serif 4', serif; letter-spacing: -0.01em; }

        .dna-card {
            background: #FBFAF8;
            border: 1px solid #E4E0D8;
            border-left: 4px solid #1B4B4F;
            border-radius: 6px;
            padding: 1.25rem 1.5rem;
            margin-top: 0.5rem;
        }
        .dna-quote {
            font-family: 'Source Serif 4', serif;
            font-style: italic;
            font-size: 1.02rem;
            color: #333;
            line-height: 1.5;
            margin-bottom: 1rem;
        }
        .dna-chips { margin-bottom: 0.6rem; }
        .dna-chip {
            display: inline-block;
            background: #E9EFEF;
            color: #1B4B4F;
            border-radius: 999px;
            padding: 0.15rem 0.7rem;
            font-size: 0.82rem;
            margin-right: 0.4rem;
            margin-bottom: 0.3rem;
        }
        .dna-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.88rem;
            color: #555;
            padding: 0.25rem 0;
            border-top: 1px solid #EEEAE0;
        }
        .dna-row span:first-child { color: #888; }
        .dna-row span:last-child { font-weight: 600; color: #1B4B4F; }

        .rx-card {
            background: #FFFFFF;
            border: 1px solid #E4E0D8;
            border-radius: 6px;
            padding: 1.1rem 1.4rem;
            margin-bottom: 0.9rem;
            display: flex;
            gap: 1rem;
            align-items: flex-start;
        }
        .rx-rank {
            font-family: 'Source Serif 4', serif;
            font-size: 1.6rem;
            font-weight: 700;
            color: #D8D2C4;
            line-height: 1;
            min-width: 2rem;
        }
        .rx-name { font-weight: 600; font-size: 1.02rem; color: #1B1B1B; margin-bottom: 0.3rem; }
        .rx-score-track { background: #EEEAE0; border-radius: 999px; height: 6px; width: 100%; margin: 0.4rem 0 0.7rem 0; }
        .rx-score-fill { background: #1B4B4F; border-radius: 999px; height: 6px; }
        .rx-score-label { font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; }
        .rx-reason { font-size: 0.88rem; color: #444; margin: 0.15rem 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def dna_card(dna):
    chips = "".join(f'<span class="dna-chip">{a.replace("_", " ")}</span>' for a in dna["top_audiences"])
    html = f"""
    <div class="dna-card">
        <div class="dna-quote">"{dna['character']}"</div>
        <div class="dna-chips">{chips}</div>
        <div class="dna-row"><span>Food demand</span><span>{dna['food_demand']:.2f}</span></div>
        <div class="dna-row"><span>Retail demand</span><span>{dna['retail_demand']:.2f}</span></div>
        <div class="dna-row"><span>Anchor</span><span>{dna['anchor']}</span></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def rx_card(rank, prescription, reasons_text):
    pct = min(100, max(0, prescription["score"] * 100))
    # reasons come back as a "✓ ..." string, one reason per line — split into rows
    reason_lines = [ln.strip() for ln in reasons_text.split("\n") if ln.strip()]
    reasons_html = "".join(f'<div class="rx-reason">{ln}</div>' for ln in reason_lines)
    html = f"""
    <div class="rx-card">
        <div class="rx-rank">{rank:02d}</div>
        <div style="flex:1">
            <div class="rx-name">{prescription['name']}</div>
            <div class="rx-score-track"><div class="rx-score-fill" style="width:{pct:.0f}%"></div></div>
            <div class="rx-score-label">Fit score {prescription['score']:.2f}</div>
            {reasons_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def main():
    init_state()
    inject_css()
    st.sidebar.title("🩺 CorridorRx")
    page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

    if page == "1. Select Corridor":
        page_select()
    elif page == "2. Health Dashboard":
        require_corridor()
        page_health()
    elif page == "3. Diagnosis Report":
        require_corridor()
        page_diagnosis()
    elif page == "4. Prescription":
        require_corridor()
        page_prescription()
    elif page == "5. Impact Simulator":
        require_corridor()
        page_simulator()
    elif page == "6. Impact Results":
        require_corridor()
        page_results()
    elif page == "Ask the Corridor":
        require_corridor()
        page_chat()


def page_select():
    st.title("Select a Corridor")
    st.write("Pick a commercial corridor to run through the CorridorRx diagnosis.")

    options = data_prep.corridor_list()
    labels = [name for _, name in options]
    ids = [cid for cid, _ in options]

    default_idx = ids.index(st.session_state.corridor_id) if st.session_state.corridor_id in ids else 0
    choice = st.selectbox("Corridor", labels, index=default_idx)
    selected_id = ids[labels.index(choice)]

    if st.button("Run Check-up →", type="primary"):
        st.session_state.corridor_id = selected_id
        st.session_state.sim_result = None
        st.rerun()


def page_health():
    profile = data_prep.get_corridor_profile(st.session_state.corridor_id)
    dna = profile["dna"]

    st.title(profile["corridor"]["name"])
    st.caption(dna["character"])

    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(gauge_chart(profile["health_score"], profile["status"]), use_container_width=True)
    with col2:
        st.plotly_chart(radar_chart(profile["sub_scores"]), use_container_width=True)

    st.subheader("Corridor DNA")
    dna_card(dna)


def page_diagnosis():
    profile = data_prep.get_corridor_profile(st.session_state.corridor_id)
    st.title("Diagnosis Report")
    st.metric("Health Score", f'{profile["health_score"]} / 100', profile["status"])

    st.subheader("Problems identified")
    for fact in profile["diagnosis_facts"]:
        st.markdown(f"- {fact.capitalize()}")

    st.subheader("Doctor's note")
    with st.spinner("Writing diagnosis..."):
        note = llm_engine.diagnosis_report(profile["diagnosis_facts"], profile["dna"]["character"])
    st.write(note)


def page_prescription():
    profile = data_prep.get_corridor_profile(st.session_state.corridor_id)
    st.title("Prescription")
    st.write("Top-fitting concepts, ranked by this corridor's own archetype-matching scores.")

    for i, p in enumerate(profile["prescriptions"], start=1):
        reasons = llm_engine.prescription_reasons(p, profile["dna"])
        rx_card(i, p, reasons)


def page_simulator():
    st.title("Impact Simulator")
    st.write("Pick an intervention and see how the health score responds, recomputed from real data — not a scripted number.")

    intervention = st.selectbox("Simulate:", list(data_prep.INTERVENTIONS.keys()))

    if st.button("Run Simulation", type="primary"):
        result = data_prep.simulate_impact(st.session_state.corridor_id, intervention)
        st.session_state.sim_result = result
        st.success("Simulation complete — see Page 6: Impact Results.")


def page_results():
    if not st.session_state.sim_result:
        st.info("Run a simulation on Page 5 first.")
        return

    result = st.session_state.sim_result
    st.title("Impact Results")
    st.subheader(result["intervention"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Before", result["before_score"])
    c2.metric("After", result["after_score"], delta=result["delta"])
    c3.metric("Change", f'{result["delta"]:+d} pts')

    st.plotly_chart(before_after_bar(result["before_sub"], result["after_sub"]), use_container_width=True)

    st.subheader("Why this changed")
    profile = data_prep.get_corridor_profile(st.session_state.corridor_id)
    narrative = llm_engine.impact_narrative(result, profile["dna"]["character"])
    st.write(narrative)


def page_chat():
    st.title("Ask the Corridor")
    profile = data_prep.get_corridor_profile(st.session_state.corridor_id)

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    question = st.chat_input("Ask a question about this corridor...")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.write(question)
        answer = llm_engine.ask_the_corridor(profile, question)
        st.session_state.chat_history.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.write(answer)


if __name__ == "__main__":
    main()