import streamlit as st
import os
import sys

# Ensure local project directory is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# =====================================================================
# IMPORT BACKEND MODULES
# =====================================================================

try:
    from agent import (
        get_proactive_checkin_question,
        process_employee_response,
        recall_updated_context,
        generate_manager_dashboard_summary,
        EMPLOYEE_NAMES,
        HINDSIGHT_API_KEY,
        GROQ_API_KEY,
    )

    from mock_events import get_mock_signals_for_employee

except ImportError as e:
    st.error(f"Error loading agent modules: {e}")
    st.stop()


# =====================================================================
# PAGE CONFIGURATION
# =====================================================================

st.set_page_config(
    page_title="Daily Operations Synthesizer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================================
# CUSTOM CSS
# =====================================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 20px;
        color: #777;
        margin-bottom: 30px;
    }

    .agent-question {
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    .agent-question-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .agent-question-text {
        font-size: 22px;
        font-weight: 500;
    }

    .success-box {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2e7d32;
        margin-top: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# SIDEBAR NAVIGATION & SYSTEM STATUS
# =====================================================================

with st.sidebar:

    st.title("🤖 Navigation")

    view_mode = st.radio(
        "Select Portal View:",
        [
            "👤 Employee Check-In",
            "👔 Manager Dashboard",
        ],
        index=0,
    )

    st.divider()

    st.subheader("⚙️ System Status")

    h_status = (
        "🟢 Connected"
        if HINDSIGHT_API_KEY
        and HINDSIGHT_API_KEY != "your_hindsight_api_key_here"
        else "🔴 Key Missing"
    )

    g_status = (
        "🟢 Connected"
        if GROQ_API_KEY
        and GROQ_API_KEY != "gsk_your_groq_api_key_here"
        else "🔴 Key Missing"
    )

    st.write(f"**Hindsight Memory:** {h_status}")
    st.write(f"**Groq LLM Engine:** {g_status}")
    st.write("**Model:** `openai/gpt-oss-20b`")

    st.divider()

    st.subheader("🧠 Active Memory Banks")

    st.code(
        """emp_alice
emp_bob
emp_charlie
team_ops""",
        language="text",
    )

    st.caption(
        "HackwithHyderabad 3.0 | Hindsight Memory Agent"
    )


# =====================================================================
# VIEW 1: EMPLOYEE DAILY CHECK-IN
# =====================================================================

if view_mode == "👤 Employee Check-In":

    st.markdown(
        '<div class="main-title">Daily Operations Synthesizer</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Zero-Friction Proactive Verification Agent"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])

    # ---------------------------------------------------------------
    # LEFT COLUMN
    # ---------------------------------------------------------------

    with col1:

        st.subheader("1. Select Employee")

        emp_key = st.selectbox(
            "Choose active team member:",
            options=list(EMPLOYEE_NAMES.keys()),
            format_func=lambda x: EMPLOYEE_NAMES[x],
        )

        emp_name = EMPLOYEE_NAMES[emp_key]

        st.info(
            "💡 **Zero-Friction Goal:** "
            "The agent inspects background activity + Hindsight memory "
            "to ask ONE targeted verification question. "
            "You only confirm in 3 seconds!"
        )

        if st.button(
            "🚀 Start Check-In Flow",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "Retrieving background signals & Hindsight memory..."
            ):

                st.session_state["checkin_data"] = (
                    get_proactive_checkin_question(emp_key)
                )

                st.session_state["response_submitted"] = False

                # Clear previous result
                if "result_data" in st.session_state:
                    del st.session_state["result_data"]

    # ---------------------------------------------------------------
    # RIGHT COLUMN
    # ---------------------------------------------------------------

    with col2:

        if (
            "checkin_data" in st.session_state
            and st.session_state["checkin_data"]["employee_id"]
            == emp_key
        ):

            data = st.session_state["checkin_data"]

            st.subheader(
                "2. Context Fusion & Question Generation"
            )

            # -------------------------------------------------------
            # DAY 10 SIGNALS
            # -------------------------------------------------------

            with st.expander(
                "🧠 **View Hindsight TEMPR Recalled Context**",
                expanded=False,
            ):

                # Use freshly recalled memory after submission,
                # otherwise use the original check-in recall.
                if st.session_state.get("response_submitted", False):

                    refreshed_context = st.session_state.get(
                        "updated_context",
                        {},
                    )

                    personal_context = refreshed_context.get(
                        "personal_context",
                        "No updated personal context available.",
                    )

                    team_context = refreshed_context.get(
                        "team_context",
                        "No updated team context available.",
                    )

                    st.success("🔄 Showing freshly recalled Hindsight memory")

                else:

                    personal_context = data.get(
                        "personal_context",
                        "No personal context available.",
                    )

                    team_context = data.get(
                        "team_context",
                        "No team context available.",
                    )

                st.markdown(
                    f"**Personal Memory (`{emp_key}`):**"
                )

                st.text(personal_context)

                st.markdown(
                    "**Team Dependencies (`team_ops`):**"
                )

                st.text(team_context)
            # -------------------------------------------------------
            # PROACTIVE QUESTION
            # -------------------------------------------------------

            with st.container(border=True):
                st.markdown("### 📩 Agent Question")

                st.info(
                    data["proactive_question"]
                )

            # -------------------------------------------------------
            # RESPONSE
            # -------------------------------------------------------

            st.subheader(
                "3. Minimal 3-Second Response"
            )

            st.caption(
                "Quick response presets:"
            )

            preset_cols = st.columns(3)

            quick_reply = None

            with preset_cols[0]:

                if st.button(
                    "Yep, pushed to staging",
                    use_container_width=True,
                ):
                    quick_reply = "Yep, pushed to staging."

            with preset_cols[1]:

                if st.button(
                    "Done, 100% resolved",
                    use_container_width=True,
                ):
                    quick_reply = "Done, 100% resolved."

            with preset_cols[2]:

                if st.button(
                    "Blocked by QA testing",
                    use_container_width=True,
                ):
                    quick_reply = "Blocked by QA testing."

            # -------------------------------------------------------
            # RESPONSE INPUT
            # -------------------------------------------------------

            if quick_reply:

                st.session_state["quick_reply"] = quick_reply

            user_reply = st.text_input(
                "Type your short response:",
                value=st.session_state.get(
                    "quick_reply",
                    "",
                ),
                placeholder="e.g. Yep, pushed to staging.",
            )

            # -------------------------------------------------------
            # SUBMIT RESPONSE
            # -------------------------------------------------------

            if st.button(
                "💾 Submit & Retain Update",
                type="primary",
                use_container_width=True,
            ):

                if not user_reply.strip():

                    st.warning(
                        "Please enter a short response "
                        "or click a preset above."
                    )

                else:

                    with st.spinner(
                        "Interpreting response and "
                        "retaining into Hindsight memory banks..."
                    ):

                       result = process_employee_response(
                        emp_key,
                        user_reply,
                        data["proactive_question"],
                    )

                    # Re-recall Hindsight after the retain operation
                    updated_context = recall_updated_context(emp_key)

                    st.session_state["result_data"] = result

                    st.session_state["updated_context"] = updated_context

                    st.session_state[
                        "response_submitted"
                    ] = True

            # -------------------------------------------------------
            # RETENTION RESULT
            # -------------------------------------------------------

            if st.session_state.get(
                "response_submitted",
                False,
            ):

                res = st.session_state["result_data"]

                st.success(
                    f"✅ {res['message']}"
                )

                st.markdown(
                    f"""
                    <div class="success-box">

                    <b>💡 Factual Interpretation
                    (Saved to Memory):</b>

                    <br><br>

                    <i>"{res['factual_update']}"</i>

                    <br><br>

                    <b>Timestamp:</b>
                    {res['timestamp']}

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.caption(
                    f"🔒 **Dual Retain Executed:** "
                    f"Full context saved to `{emp_key}`, "
                    f"concise fact saved to `team_ops`."
                )


# =====================================================================
# VIEW 2: MANAGER EXECUTIVE DASHBOARD
# =====================================================================

elif view_mode == "👔 Manager Dashboard":

    st.markdown(
        '<div class="main-title">'
        "Executive Manager Operations Dashboard"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Real-Time Team Context Synthesis powered by "
        "Hindsight Reflection"
        "</div>",
        unsafe_allow_html=True,
    )

    col_btn, col_info = st.columns([1, 2])

    # ---------------------------------------------------------------
    # GENERATE REPORT BUTTON
    # ---------------------------------------------------------------

    with col_btn:

        generate_btn = st.button(
            "📊 Generate Executive Operations Report",
            type="primary",
            use_container_width=True,
        )

    with col_info:

        st.info(
            "The manager view synthesizes operational "
            "context across employee and team memory banks."
        )

    # ---------------------------------------------------------------
    # GENERATE REPORT
    # ---------------------------------------------------------------

    if generate_btn:

        with st.spinner(
            "Executing Hindsight reflect() across all "
            "active memory banks..."
        ):

            report = generate_manager_dashboard_summary()

            st.session_state["manager_report"] = report

    # ---------------------------------------------------------------
    # DISPLAY REPORT
    # ---------------------------------------------------------------

    if "manager_report" in st.session_state:

        st.markdown("---")

        st.markdown(
            st.session_state["manager_report"]
        )

    else:

        st.info(
            "👆 Click the button above to synthesize "
            "cross-employee operational memory."
        )


# =====================================================================
# FOOTER
# =====================================================================

st.divider()

st.caption(
    "🤖 Daily Operations Synthesizer • "
    "HackwithHyderabad 3.0 • "
    "Powered by Hindsight + Groq"
)