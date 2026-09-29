import os
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv


# ============================================================
# LOGGING & ENVIRONMENT
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

load_dotenv()


# ============================================================
# API KEYS
# ============================================================

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ============================================================
# MOCK EVENTS
# ============================================================

try:
    from mock_events import (
        MOCK_DAY10_SIGNALS,
        EMPLOYEE_NAMES,
        get_mock_signals_for_employee
    )

except ImportError:
    logging.warning(
        "mock_events.py not found. "
        "Falling back to default mock signal handler."
    )

    MOCK_DAY10_SIGNALS = {}

    EMPLOYEE_NAMES = {
        "emp_alice": "Alice (Backend Lead)",
        "emp_bob": "Bob (Frontend Lead)",
        "emp_charlie": "Charlie (DevOps Lead)"
    }

    def get_mock_signals_for_employee(emp_id):
        return ["No background signals recorded today."]


# ============================================================
# CLIENT INITIALIZATION
# ============================================================

hindsight_client = None
groq_client = None


def initialize_clients():

    global hindsight_client
    global groq_client

    # --------------------------------------------------------
    # Hindsight
    # --------------------------------------------------------

    if (
        not HINDSIGHT_API_KEY
        or HINDSIGHT_API_KEY.strip()
        in ["", "your_hindsight_api_key_here"]
    ):
        logging.error(
            "Missing or invalid HINDSIGHT_API_KEY "
            "in environment or .env file."
        )

        print(
            "❌ ERROR: HINDSIGHT_API_KEY is missing. "
            "Please set it in your .env file."
        )

    else:
        try:
            from hindsight_client import Hindsight

            hindsight_client = Hindsight(
                base_url=HINDSIGHT_BASE_URL,
                api_key=HINDSIGHT_API_KEY
            )

        except Exception as e:

            logging.error(
                "Failed to initialize Hindsight client."
            )

            print(
                f"❌ ERROR: Could not connect to Hindsight Cloud. "
                f"({type(e).__name__})"
            )

    # --------------------------------------------------------
    # Groq
    # --------------------------------------------------------

    if (
        not GROQ_API_KEY
        or GROQ_API_KEY.strip()
        in ["", "gsk_your_groq_api_key_here"]
    ):
        logging.error(
            "Missing or invalid GROQ_API_KEY "
            "in environment or .env file."
        )

        print(
            "❌ ERROR: GROQ_API_KEY is missing. "
            "Please set it in your .env file."
        )

    else:
        try:
            from openai import OpenAI

            groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_API_KEY
            )

        except Exception as e:

            logging.error(
                "Failed to initialize Groq "
                "OpenAI-compatible client."
            )

            print(
                f"❌ ERROR: Could not initialize Groq client. "
                f"({type(e).__name__})"
            )


# Initialize clients
initialize_clients()


MODEL_NAME = "openai/gpt-oss-20b"


# ============================================================
# HINDSIGHT RECALL PARSER
# ============================================================

def extract_recall_text(response) -> str:
    """
    Safely extracts text from a Hindsight recall response.

    Primary response structure:
        response.results

    Includes fallbacks for older/different response formats.
    """

    if response is None:
        return "No memory records retrieved."

    results = getattr(
        response,
        "results",
        None
    )

    if results is None and isinstance(response, dict):
        results = response.get("results")

    # Backward compatibility
    if results is None:
        results = getattr(
            response,
            "memories",
            None
        )

    if results is None and isinstance(response, dict):
        results = response.get("memories")

    if results is None:
        results = response

    if isinstance(results, list):

        items = []

        for item in results:

            if isinstance(item, str):
                items.append(item)

            elif isinstance(item, dict):

                text_val = (
                    item.get("text")
                    or item.get("content")
                    or item.get("memory")
                    or str(item)
                )

                items.append(text_val)

            elif hasattr(item, "text"):

                items.append(
                    getattr(item, "text")
                )

            elif hasattr(item, "content"):

                items.append(
                    getattr(item, "content")
                )

            else:
                items.append(str(item))

        if items:
            return "\n".join(
                f"- {item}"
                for item in items
            )

        return "No memory records retrieved."

    return str(results).strip()


# ============================================================
# HINDSIGHT REFLECT PARSER
# ============================================================

def extract_reflect_text(response) -> str:
    """
    Safely extracts text from a Hindsight reflect response.

    Primary response structure:
        response.text
    """

    if response is None:
        return "No reflection text generated."

    text = getattr(
        response,
        "text",
        None
    )

    if text is None and isinstance(response, dict):
        text = response.get("text")

    # Backward compatibility
    if text is None:
        text = getattr(
            response,
            "observations",
            None
        )

    if text is None and isinstance(response, dict):
        text = response.get("observations")

    if text is None:
        text = str(response)

    return str(text).strip()

def recall_updated_context(employee_id: str) -> dict:
    """
    Re-recall the employee and team memory after a new update
    has been retained in Hindsight.
    """

    personal_context = "No personal context available."
    team_context = "No team context available."

    if not hindsight_client:
        return {
            "personal_context": personal_context,
            "team_context": team_context,
        }

    # --------------------------------------------------------
    # Employee memory
    # --------------------------------------------------------

    try:
        personal_recall_resp = hindsight_client.recall(
            bank_id=employee_id,
            query=(
                "What are the most recent operational updates, "
                "completed work, blockers, and employee responses?"
            ),
        )

        personal_context = extract_recall_text(
            personal_recall_resp
        )

    except Exception as e:
        logging.warning(
            f"Hindsight personal refresh failed "
            f"for '{employee_id}': {e}"
        )

    # --------------------------------------------------------
    # Team memory
    # --------------------------------------------------------

    try:
        team_recall_resp = hindsight_client.recall(
            bank_id="team_ops",
            query=(
                "What are the most recent cross-team operational "
                "updates, completed work, blockers, and dependencies?"
            ),
        )

        team_context = extract_recall_text(
            team_recall_resp
        )

    except Exception as e:
        logging.warning(
            f"Hindsight team_ops refresh failed: {e}"
        )

    return {
        "personal_context": personal_context,
        "team_context": team_context,
    }
# ============================================================
# PROACTIVE CHECK-IN QUESTION GENERATOR
# ============================================================

def get_proactive_checkin_question(
    employee_id: str
) -> dict:
    """
    Steps 2–6:

    Fuses:
        Day 10 raw signals
        +
        Hindsight employee memory
        +
        Hindsight team_ops memory

    to generate ONE targeted,
    zero-friction verification question.
    """

    employee_name = EMPLOYEE_NAMES.get(
        employee_id,
        employee_id
    )

    # --------------------------------------------------------
    # Step 2: Load Day 10 signals
    # --------------------------------------------------------

    raw_signals = get_mock_signals_for_employee(
        employee_id
    )

    print(
        f"\n🔍 [Step 2] Loaded Day 10 raw activity "
        f"signals for {employee_name}:"
    )

    for sig in raw_signals:
        print(f" • {sig}")

    signals_text = "\n".join(
        f"- {signal}"
        for signal in raw_signals
    )

    # --------------------------------------------------------
    # Step 3: Personal Hindsight recall
    # --------------------------------------------------------

    print(
        f"\n🧠 [Step 3] Executing Hindsight "
        f"TEMPR Recall on personal bank: "
        f"'{employee_id}'..."
    )

    personal_context = (
        "No previous individual history found."
    )

    if hindsight_client:

        try:

            personal_recall_resp = (
                hindsight_client.recall(
                    bank_id=employee_id,
                    query=(
                        "What ongoing tasks, blockers, "
                        "or tickets was this employee "
                        "working on recently?"
                    )
                )
            )

            personal_context = extract_recall_text(
                personal_recall_resp
            )

        except Exception as e:

            logging.warning(
                f"Hindsight personal recall failed "
                f"for '{employee_id}': {e}"
            )

            print(
                f" ⚠️ Could not retrieve personal memory "
                f"for {employee_id}. "
                f"Proceeding with signal context."
            )

    # --------------------------------------------------------
    # Step 4: Team Hindsight recall
    # --------------------------------------------------------

    print(
        "\n🌐 [Step 4] Executing Hindsight "
        "TEMPR Recall on team bank: 'team_ops'..."
    )

    team_context = (
        "No team operations history found."
    )

    if hindsight_client:

        try:

            team_recall_resp = (
                hindsight_client.recall(
                    bank_id="team_ops",
                    query=(
                        "What cross-team deployment "
                        "updates or blockers were recently "
                        "resolved or created?"
                    )
                )
            )

            team_context = extract_recall_text(
                team_recall_resp
            )

        except Exception as e:

            logging.warning(
                f"Hindsight team_ops recall failed: {e}"
            )

            print(
                " ⚠️ Could not retrieve team_ops memory. "
                "Proceeding with personal context."
            )

    # --------------------------------------------------------
    # Step 5 & 6: Groq reasoning
    # --------------------------------------------------------

    print(
        "\n⚡ [Step 5 & 6] Groq reasoning over context "
        "-> Generating ONE contextual question..."
    )

    if not groq_client:

        fallback_q = (
            f"I noticed automated activity for "
            f"{employee_name}. "
            f"Could you confirm if your task is "
            f"on track for deployment?"
        )

        return {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "raw_signals": raw_signals,
            "personal_context": personal_context,
            "team_context": team_context,
            "proactive_question": fallback_q
        }

    prompt = f"""
You are an Enterprise Proactive Operations Agent
conducting a zero-friction, 3-second daily check-in
with {employee_name}.

CONTEXT PROVIDED:

1. RAW DAY 10 AUTOMATED SIGNALS
(System Activity Evidence from GitHub/CI/CD today):

{signals_text}

2. HISTORICAL EMPLOYEE MEMORY
(from Hindsight Memory Bank '{employee_id}'):

{personal_context}

3. CROSS-TEAM DEPENDENCIES
(from Hindsight Memory Bank 'team_ops'):

{team_context}


REASONING STEPS:

1. Determine what is ALREADY KNOWN and completed
   based on system activity evidence and past memory.

2. Identify what previous task or blocker was unresolved,
   or what dependency was recently cleared.

3. Determine what specific information is STILL UNCERTAIN
   such as final verification, an unblocked next step,
   or a remaining blocker.

4. Formulate EXACTLY ONE concise,
   highly specific verification question.


STRICT INSTRUCTIONS:

- Treat automated system activity as evidence,
  NOT employee confirmation.

- NEVER ask open-ended questions like:
  "What did you do today?"
  or
  "Can you summarize your work?"

- DO NOT ask the employee to repeat information
  that is already established in the system activity.

- Focus strictly on unresolved status, next steps,
  blockers, dependencies, or final confirmation.

- NEVER invent facts or hallucinate unmentioned tasks
  or tools.

- Generate ONLY ONE single question.

- The question must be 1–2 sentences maximum.

- Keep it extremely simple for the employee
  to answer in a few words.

PROACTIVE QUESTION:
"""

    try:

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        if not response or not response.choices:
            raise ValueError(
                "Empty completion response received "
                "from Groq API."
            )

        question = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

    except Exception as e:

        logging.error(
            f"Groq question generation failed: {e}"
        )

        question = (
            f"I observed today's background activity "
            f"for {employee_name}. "
            f"Is everything ready for the upcoming "
            f"release, or is anything blocked?"
        )

    return {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "raw_signals": raw_signals,
        "personal_context": personal_context,
        "team_context": team_context,
        "proactive_question": question
    }


# ============================================================
# INTERPRET SHORT EMPLOYEE RESPONSE
# ============================================================

def interpret_short_response(
    employee_name: str,
    question_asked: str,
    user_response: str
) -> str:
    """
    Converts a short employee response into
    a concise factual statement.
    """

    if not user_response or not user_response.strip():

        return (
            f"{employee_name} provided an empty "
            f"check-in response."
        )

    if not groq_client:

        return (
            f"{employee_name} responded: "
            f"'{user_response.strip()}' "
            f"in response to '{question_asked}'."
        )

    prompt = f"""
Convert the employee's short response into a single,
concise, unambiguous factual statement.

Employee Name:
{employee_name}

Question Asked / Context:
{question_asked}

Short Employee Response:
"{user_response}"

INSTRUCTIONS:

- Output ONLY a single factual sentence.
- Describe what happened or what the employee confirmed.
- Do NOT output extra commentary.
- Do NOT invent information.

Example:

Question:
"Is the CORS fix pushed to staging?"

Response:
"Yep"

Output:
"Alice confirmed that the CORS fix was pushed to staging."

FACTUAL STATEMENT:
"""

    try:

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )

        if response and response.choices:

            return (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

    except Exception as e:

        logging.warning(
            "Groq short response interpretation "
            f"failed: {e}"
        )

    return (
        f"{employee_name} confirmed: "
        f"'{user_response.strip()}' "
        f"regarding '{question_asked}'."
    )


# ============================================================
# PROCESS & RETAIN EMPLOYEE RESPONSE
# ============================================================

def process_employee_response(
    employee_id: str,
    user_response: str,
    question_asked: str
) -> dict:
    """
    Steps 7–9:

    1. Interpret short response.
    2. Create timestamped employee memory.
    3. Retain full context in employee bank.
    4. Retain concise fact in team_ops.
    """

    employee_name = EMPLOYEE_NAMES.get(
        employee_id,
        employee_id
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --------------------------------------------------------
    # Step 8: Interpret response
    # --------------------------------------------------------

    factual_update = interpret_short_response(
        employee_name,
        question_asked,
        user_response
    )

    # --------------------------------------------------------
    # Employee bank entry
    # --------------------------------------------------------

    employee_bank_entry = (
        f"[{timestamp}] "
        f"Employee Update for {employee_name}\n"
        f"Context/Question: {question_asked}\n"
        f"Raw Response: \"{user_response}\"\n"
        f"Factual Interpretation: {factual_update}"
    )

    # --------------------------------------------------------
    # Team bank entry
    # --------------------------------------------------------

    team_ops_entry = (
        f"[{timestamp}] {factual_update}"
    )

    # --------------------------------------------------------
    # Step 9: Retain in Hindsight
    # --------------------------------------------------------

    if hindsight_client:

        print(
            f"\n💾 [Step 9] Committing update to "
            f"Hindsight bank '{employee_id}'..."
        )

        try:

            hindsight_client.retain(
                bank_id=employee_id,
                content=employee_bank_entry
            )

        except Exception as e:

            logging.error(
                f"Failed to retain update to "
                f"'{employee_id}': {e}"
            )

            print(
                f" ⚠️ Retain operation failed for "
                f"bank '{employee_id}'."
            )

        print(
            "🌐 [Step 9] Syncing concise fact "
            "to shared bank 'team_ops'..."
        )

        try:

            hindsight_client.retain(
                bank_id="team_ops",
                content=team_ops_entry
            )

        except Exception as e:

            logging.error(
                f"Failed to retain update to "
                f"'team_ops': {e}"
            )

            print(
                " ⚠️ Retain operation failed "
                "for 'team_ops'."
            )

    else:

        print(
            "\n⚠️ Hindsight client offline. "
            "Skipping live memory retention."
        )

    return {
        "status": "success",
        "timestamp": timestamp,
        "factual_update": factual_update,
        "message": (
            f"Update successfully saved to "
            f"Hindsight memory for {employee_name}!"
        )
    }


# ============================================================
# MANAGER EXECUTIVE DASHBOARD
# ============================================================

def generate_manager_dashboard_summary() -> str:
    """
    Step 10:

    Gathers operational context from:
        emp_alice
        emp_bob
        emp_charlie
        team_ops

    Uses Hindsight reflect/recall and Groq to
    produce an executive status report.
    """

    print(
        "\n📊 [Step 10] Gathering operational context "
        "across emp_alice, emp_bob, emp_charlie, team_ops..."
    )

    all_reflections = []

    target_banks = [
        "emp_alice",
        "emp_bob",
        "emp_charlie",
        "team_ops"
    ]

    for bank_id in target_banks:

        if not hindsight_client:

            all_reflections.append(
                f"--- Bank: {bank_id} ---\n"
                "No live memory connection available."
            )

            continue

        try:

            reflect_resp = hindsight_client.reflect(
                bank_id=bank_id,
                query=(
                    "What are the current operational "
                    "observations, completed milestones, "
                    "and active bottlenecks?"
                )
            )

            obs = extract_reflect_text(
                reflect_resp
            )

            all_reflections.append(
                f"--- Bank: {bank_id} ---\n{obs}"
            )

        except Exception as e:

            logging.info(
                f"Reflect failed for bank '{bank_id}', "
                f"falling back to TEMPR recall: {e}"
            )

            try:

                recall_resp = hindsight_client.recall(
                    bank_id=bank_id,
                    query=(
                        "Summary of current operational "
                        "status, completed work, "
                        "and unresolved blockers"
                    )
                )

                all_reflections.append(
                    f"--- Bank: {bank_id} ---\n"
                    f"{extract_recall_text(recall_resp)}"
                )

            except Exception as recall_err:

                logging.error(
                    f"Recall fallback also failed "
                    f"for bank '{bank_id}': {recall_err}"
                )

                all_reflections.append(
                    f"--- Bank: {bank_id} ---\n"
                    "Unable to retrieve memory."
                )

    combined_reflections = "\n\n".join(
        all_reflections
    )

    # --------------------------------------------------------
    # Offline mode
    # --------------------------------------------------------

    if not groq_client:

        return (
            "### Executive Summary (Offline Mode)\n\n"
            "Collected Context:\n"
            f"{combined_reflections}"
        )

    print(
        "⚡ Generating Manager Executive Dashboard "
        "via Groq..."
    )

    prompt = f"""
You are an Executive Operations Assistant.

Synthesize the following Hindsight memory context
from these team banks:

- emp_alice
- emp_bob
- emp_charlie
- team_ops

REFLECTED MEMORY DATA:

{combined_reflections}

INSTRUCTIONS:

- Focus on current progress.
- Focus on completed work.
- Identify unresolved blockers.
- Identify dependencies.
- Identify risks and uncertainties.
- Highlight important team updates.
- Do NOT expose raw conversational transcripts.
- Do NOT expose internal debug information.
- Do NOT invent facts.
- Present a concise operational overview.

FORMAT:

1. 🎯 Current Progress & Completed Milestones

2. ⚠️ Active Blockers & Dependencies

3. 🚀 Release Risks & Next Steps

4. 📈 Team Operational Velocity

Use clean markdown headers and concise bullet points.
"""

    try:

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        if response and response.choices:

            return (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

    except Exception as e:

        logging.error(
            "Groq manager dashboard synthesis "
            f"failed: {e}"
        )

    return (
        "### Executive Operations Summary\n\n"
        "*Gathered Memory Context*:\n"
        f"{combined_reflections}"
    )


# ============================================================
# COMPLETE DEMO FLOW
# ============================================================

def run_complete_demo():

    print(
        "=================================================================="
    )

    print(
        "🤖 DAILY OPERATIONS SYNTHESIZER — COMPLETE DEMO FLOW"
    )

    print(
        "=================================================================="
    )

    # --------------------------------------------------------
    # Step 1
    # --------------------------------------------------------

    print(
        "\n📌 [Step 1] Initializing demo with "
        "existing Days 1–9 seeded Hindsight memories."
    )

    print(
        " Memory Banks Active: "
        "'emp_alice', 'emp_bob', "
        "'emp_charlie', 'team_ops'"
    )

    # Target employee
    target_emp = "emp_alice"

    # --------------------------------------------------------
    # Steps 2–6
    # --------------------------------------------------------

    checkin_data = get_proactive_checkin_question(
        target_emp
    )

    print(
        "\n------------------------------------------------------------------"
    )

    print(
        f"📩 [Step 6] PROACTIVE QUESTION GENERATED "
        f"FOR {checkin_data['employee_name']}:"
    )

    print(
        "------------------------------------------------------------------"
    )

    print(
        f"\"{checkin_data['proactive_question']}\""
    )

    print(
        "------------------------------------------------------------------"
    )

    # --------------------------------------------------------
    # Step 7
    # --------------------------------------------------------

    simulated_user_reply = (
        "Yep, pushed to staging."
    )

    print(
        f"\n👤 [Step 7] MINIMAL EMPLOYEE RESPONSE "
        f"RECEIVED: \"{simulated_user_reply}\""
    )

    # --------------------------------------------------------
    # Steps 8–9
    # --------------------------------------------------------

    process_result = process_employee_response(
        employee_id=target_emp,
        user_response=simulated_user_reply,
        question_asked=checkin_data[
            "proactive_question"
        ]
    )

    print(
        f"💡 [Step 8] FACTUAL INTERPRETATION: "
        f"{process_result['factual_update']}"
    )

    print(
        f"✅ {process_result['message']}"
    )

    # --------------------------------------------------------
    # Step 10
    # --------------------------------------------------------

    print(
        "\n------------------------------------------------------------------"
    )

    print(
        "👔 [Step 10] GENERATING MANAGER "
        "EXECUTIVE DASHBOARD"
    )

    print(
        "------------------------------------------------------------------"
    )

    dashboard_report = (
        generate_manager_dashboard_summary()
    )

    print(dashboard_report)

    print(
        "\n=================================================================="
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    try:
        run_complete_demo()
    finally:
        try:
            hindsight_client.close()
        except Exception:
            pass

        try:
            groq_client.close()
        except Exception:
            pass