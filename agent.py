import os
import sys
import logging
import asyncio
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from openai import OpenAI

# =====================================================================
# CONFIGURATION
# =====================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = "openai/gpt-oss-20b"


# =====================================================================
# MOCK SIGNALS
# =====================================================================

try:
    from mock_events import (
        MOCK_DAY10_SIGNALS,
        EMPLOYEE_NAMES,
        get_mock_signals_for_employee,
    )

except ImportError:
    logging.warning(
        "mock_events.py not found. Using fallback mock signal handler."
    )

    MOCK_DAY10_SIGNALS = {}

    EMPLOYEE_NAMES = {
        "emp_alice": "Alice (Backend Lead)",
        "emp_bob": "Bob (Frontend Lead)",
        "emp_charlie": "Charlie (DevOps Lead)",
    }

    def get_mock_signals_for_employee(employee_id: str) -> list:
        return ["No background signals recorded today."]


# =====================================================================
# CLIENT INITIALIZATION
# =====================================================================

# IMPORTANT:
# We intentionally do NOT keep a long-lived Hindsight HTTP client here.
#
# Streamlit reruns can interact badly with the aiohttp session used by
# the Hindsight SDK when the synchronous wrapper is reused across
# different execution contexts.
#
# Instead, every Hindsight operation creates its own client inside
# its own asyncio event loop and closes it afterwards.

hindsight_client = None
groq_client = None


def initialize_clients():
    """
    Initialize the Groq client.

    Hindsight is initialized lazily inside each async operation.
    """

    global groq_client

    # ---------------------------------------------------------------
    # Validate Hindsight configuration
    # ---------------------------------------------------------------

    if (
        not HINDSIGHT_API_KEY
        or HINDSIGHT_API_KEY.strip()
        in ["", "your_hindsight_api_key_here"]
    ):
        logging.error(
            "Missing or invalid HINDSIGHT_API_KEY."
        )
        print(
            "❌ ERROR: HINDSIGHT_API_KEY is missing."
        )

    # ---------------------------------------------------------------
    # Validate Groq configuration
    # ---------------------------------------------------------------

    if (
        not GROQ_API_KEY
        or GROQ_API_KEY.strip()
        in ["", "gsk_your_groq_api_key_here"]
    ):
        logging.error(
            "Missing or invalid GROQ_API_KEY."
        )
        print(
            "❌ ERROR: GROQ_API_KEY is missing."
        )

        groq_client = None

    else:
        try:
            groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_API_KEY,
            )

        except Exception as e:
            logging.error(
                "Failed to initialize Groq client."
            )
            print(
                f"❌ ERROR: Could not initialize Groq client. "
                f"({type(e).__name__})"
            )

            groq_client = None


initialize_clients()


# =====================================================================
# HINDSIGHT ASYNC BRIDGE
# =====================================================================

def _run_hindsight_operation(operation, *args, **kwargs):
    """
    Run ONE Hindsight async operation inside a completely isolated
    asyncio event loop.

    This is intentionally used instead of the Hindsight synchronous
    wrappers because Streamlit can rerun code in different execution
    contexts.

    The Hindsight client is created INSIDE the same event loop in which
    the async request executes and is closed before the loop exits.

    This prevents errors such as:

        Timeout context manager should be used inside a task

    and:

        Unclosed client session
    """

    if not HINDSIGHT_API_KEY:
        raise RuntimeError(
            "HINDSIGHT_API_KEY is not configured."
        )

    async def _operation():

        from hindsight_client import Hindsight

        client = Hindsight(
            base_url=HINDSIGHT_BASE_URL,
            api_key=HINDSIGHT_API_KEY,
        )

        try:
            result = await operation(
                client,
                *args,
                **kwargs,
            )

            return result

        finally:
            try:
                await client.aclose()

            except Exception as close_error:
                logging.warning(
                    "Hindsight async client close failed: %s",
                    close_error,
                )

    return asyncio.run(_operation())


def _hindsight_recall(
    bank_id: str,
    query: str,
):
    """
    Streamlit-safe Hindsight recall.
    """

    async def operation(
        client,
        bank_id,
        query,
    ):
        return await client.arecall(
            bank_id=bank_id,
            query=query,
        )

    return _run_hindsight_operation(
        operation,
        bank_id,
        query,
    )


def _hindsight_retain(
    bank_id: str,
    content: str,
):
    """
    Streamlit-safe Hindsight retain.
    """

    async def operation(
        client,
        bank_id,
        content,
    ):
        return await client.aretain(
            bank_id=bank_id,
            content=content,
        )

    return _run_hindsight_operation(
        operation,
        bank_id,
        content,
    )


def _hindsight_reflect(
    bank_id: str,
    query: str,
):
    """
    Streamlit-safe Hindsight reflect.
    """

    async def operation(
        client,
        bank_id,
        query,
    ):
        return await client.areflect(
            bank_id=bank_id,
            query=query,
        )

    return _run_hindsight_operation(
        operation,
        bank_id,
        query,
    )


# =====================================================================
# HINDSIGHT RESPONSE PARSING
# =====================================================================

def extract_recall_text(response) -> str:
    """
    Safely extracts memory text from a Hindsight recall response.
    """

    if response is None:
        return "No memory records retrieved."

    results = getattr(
        response,
        "results",
        None,
    )

    if results is None and isinstance(response, dict):
        results = response.get("results")

    if results is None:
        results = getattr(
            response,
            "memories",
            None,
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


def extract_reflect_text(response) -> str:
    """
    Safely extracts text from a Hindsight reflect response.
    """

    if response is None:
        return "No reflection text generated."

    text = getattr(
        response,
        "text",
        None,
    )

    if text is None and isinstance(response, dict):
        text = response.get("text")

    if text is None:
        text = getattr(
            response,
            "observations",
            None,
        )

    if text is None and isinstance(response, dict):
        text = response.get("observations")

    if text is None:
        text = str(response)

    return str(text).strip()


# =====================================================================
# PROACTIVE CHECK-IN QUESTION GENERATOR
# =====================================================================

def get_proactive_checkin_question(
    employee_id: str,
) -> dict:
    """
    Fuses:

        Day 10 system signals
        +
        Hindsight personal memory
        +
        Hindsight team memory
        ↓
        Groq
        ↓
        ONE targeted question
    """

    employee_name = EMPLOYEE_NAMES.get(
        employee_id,
        employee_id,
    )

    raw_signals = get_mock_signals_for_employee(
        employee_id
    )

    print(
        f"\n🔍 [Step 2] Loaded Day 10 raw activity "
        f"signals for {employee_name}:"
    )

    for signal in raw_signals:
        print(f" • {signal}")

    signals_text = "\n".join(
        f"- {signal}"
        for signal in raw_signals
    )

    # ---------------------------------------------------------------
    # Hindsight Personal Recall
    # ---------------------------------------------------------------

    print(
        f"\n🧠 [Step 3] Executing Hindsight TEMPR Recall "
        f"on personal bank: '{employee_id}'..."
    )

    personal_context = (
        "No previous individual history found."
    )

    if HINDSIGHT_API_KEY:

        try:

            personal_recall_resp = _hindsight_recall(
                bank_id=employee_id,
                query=(
                    "What ongoing tasks, blockers, "
                    "or tickets was this employee "
                    "working on recently?"
                ),
            )

            personal_context = extract_recall_text(
                personal_recall_resp
            )

        except Exception as e:

            logging.warning(
                "Hindsight personal recall failed "
                "for '%s': %s",
                employee_id,
                e,
            )

            print(
                f" ⚠️ Could not retrieve personal memory "
                f"for {employee_id}."
            )

    # ---------------------------------------------------------------
    # Hindsight Team Recall
    # ---------------------------------------------------------------

    print(
        "\n🌐 [Step 4] Executing Hindsight TEMPR Recall "
        "on team bank: 'team_ops'..."
    )

    team_context = (
        "No team operations history found."
    )

    if HINDSIGHT_API_KEY:

        try:

            team_recall_resp = _hindsight_recall(
                bank_id="team_ops",
                query=(
                    "What cross-team deployment "
                    "updates or blockers were recently "
                    "resolved or created?"
                ),
            )

            team_context = extract_recall_text(
                team_recall_resp
            )

        except Exception as e:

            logging.warning(
                "Hindsight team_ops recall failed: %s",
                e,
            )

            print(
                " ⚠️ Could not retrieve team_ops memory."
            )

    # ---------------------------------------------------------------
    # Groq reasoning
    # ---------------------------------------------------------------

    print(
        "\n⚡ [Step 5 & 6] Groq reasoning over context "
        "-> Generating ONE contextual question..."
    )

    if not groq_client:

        fallback_question = (
            f"I noticed automated activity for "
            f"{employee_name}. Could you confirm "
            f"if your task is on track?"
        )

        return {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "raw_signals": raw_signals,
            "personal_context": personal_context,
            "team_context": team_context,
            "proactive_question": fallback_question,
        }

    prompt = f"""
You are an Enterprise Proactive Operations Agent
conducting a zero-friction, 3-second daily check-in
with {employee_name}.

CONTEXT PROVIDED:

1. RAW DAY 10 AUTOMATED SIGNALS
(System Activity Evidence):
{signals_text}

2. HISTORICAL EMPLOYEE MEMORY
(Hindsight Memory Bank '{employee_id}'):
{personal_context}

3. CROSS-TEAM DEPENDENCIES
(Hindsight Memory Bank 'team_ops'):
{team_context}

REASONING STEPS:

1. Determine what is ALREADY KNOWN and completed
   based on system activity evidence and past memory.

2. Identify what previous task or blocker was unresolved,
   or what dependency was recently cleared.

3. Determine what specific information is STILL UNCERTAIN.

4. Formulate EXACTLY ONE concise verification question.

STRICT INSTRUCTIONS:

- Treat automated system activity as evidence,
  NOT employee confirmation.
- NEVER ask:
  "What did you do today?"
- NEVER ask open-ended status-report questions.
- DO NOT ask the employee to repeat information already
  established by system activity.
- Focus on unresolved status, next steps, blockers,
  dependencies, or final confirmation.
- NEVER invent facts.
- NEVER hallucinate tasks or tools.
- Generate ONLY ONE question.
- Keep it extremely simple to answer in a few words.

PROACTIVE QUESTION:
"""

    try:

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.3,
        )

        if (
            not response
            or not response.choices
        ):
            raise ValueError(
                "Empty completion response."
            )

        question = (
            response.choices[0]
            .message.content
            .strip()
        )

    except Exception as e:

        logging.error(
            "Groq question generation failed: %s",
            e,
        )

        question = (
            f"I observed today's background "
            f"activity for {employee_name}. "
            f"Is everything ready for the upcoming "
            f"release, or is anything blocked?"
        )

    return {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "raw_signals": raw_signals,
        "personal_context": personal_context,
        "team_context": team_context,
        "proactive_question": question,
    }


# =====================================================================
# SHORT RESPONSE INTERPRETER
# =====================================================================

def interpret_short_response(
    employee_name: str,
    question_asked: str,
    user_response: str,
) -> str:
    """
    Converts a short employee response into a concise
    factual statement.
    """

    if (
        not user_response
        or not user_response.strip()
    ):
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
Convert the employee's short response into
a single, concise, unambiguous factual statement.

Employee Name:
{employee_name}

Question Asked / Context:
{question_asked}

Short Employee Response:
"{user_response}"

INSTRUCTIONS:

- Output ONLY one factual sentence.
- Describe ONLY what the employee's response
  explicitly confirms.
- Do NOT infer information that was not stated.
- Do NOT add extra commentary.
- Do NOT add conversational filler.

FACTUAL STATEMENT:
"""

    try:

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.1,
        )

        if response and response.choices:

            return (
                response.choices[0]
                .message.content
                .strip()
            )

    except Exception as e:

        logging.warning(
            "Groq short response interpretation failed: %s",
            e,
        )

    return (
        f"{employee_name} confirmed: "
        f"'{user_response.strip()}' "
        f"regarding '{question_asked}'."
    )


# =====================================================================
# PROCESS & RETAIN EMPLOYEE RESPONSE
# =====================================================================

def process_employee_response(
    employee_id: str,
    user_response: str,
    question_asked: str,
) -> dict:
    """
    Steps 7-9:

    1. Interpret short response.
    2. Create timestamped employee memory.
    3. Retain full context in employee bank.
    4. Retain concise fact in team_ops.
    """

    employee_name = EMPLOYEE_NAMES.get(
        employee_id,
        employee_id,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # ---------------------------------------------------------------
    # Step 8
    # ---------------------------------------------------------------

    factual_update = interpret_short_response(
        employee_name,
        question_asked,
        user_response,
    )

    employee_bank_entry = (
        f"[{timestamp}] "
        f"Employee Update for {employee_name}\n"
        f"Context/Question: {question_asked}\n"
        f"Raw Response: \"{user_response}\"\n"
        f"Factual Interpretation: {factual_update}"
    )

    team_ops_entry = (
        f"[{timestamp}] {factual_update}"
    )

    # ---------------------------------------------------------------
    # Step 9 — Employee bank
    # ---------------------------------------------------------------

    if HINDSIGHT_API_KEY:

        print(
            f"\n💾 [Step 9] Committing update to "
            f"Hindsight bank '{employee_id}'..."
        )

        try:

            _hindsight_retain(
                bank_id=employee_id,
                content=employee_bank_entry,
            )

            print(
                f" ✅ Update retained in "
                f"'{employee_id}'."
            )

        except Exception as e:

            logging.error(
                "Failed to retain update to '%s': %s",
                employee_id,
                e,
            )

            print(
                f" ⚠️ Retain operation failed for "
                f"bank '{employee_id}'."
            )

        # -----------------------------------------------------------
        # Team bank
        # -----------------------------------------------------------

        print(
            "🌐 [Step 9] Syncing concise fact "
            "to shared bank 'team_ops'..."
        )

        try:

            _hindsight_retain(
                bank_id="team_ops",
                content=team_ops_entry,
            )

            print(
                " ✅ Concise fact retained in "
                "'team_ops'."
            )

        except Exception as e:

            logging.error(
                "Failed to retain update to "
                "'team_ops': %s",
                e,
            )

            print(
                " ⚠️ Retain operation failed "
                "for 'team_ops'."
            )

    else:

        print(
            "\n⚠️ Hindsight client offline. "
            "Skipping memory retention."
        )

    return {
        "status": "success",
        "timestamp": timestamp,
        "factual_update": factual_update,
        "message": (
            f"Update successfully processed "
            f"for {employee_name}."
        ),
    }


# =====================================================================
# REFRESH HINDSIGHT CONTEXT
# =====================================================================

def recall_updated_context(
    employee_id: str,
) -> dict:
    """
    Re-recall the employee and team memory after
    a new update has been retained.
    """

    personal_context = (
        "No updated personal context available."
    )

    team_context = (
        "No updated team context available."
    )

    if not HINDSIGHT_API_KEY:

        return {
            "personal_context": personal_context,
            "team_context": team_context,
        }

    # ---------------------------------------------------------------
    # Personal memory
    # ---------------------------------------------------------------

    try:

        personal_recall_resp = _hindsight_recall(
            bank_id=employee_id,
            query=(
                "What are the most recent operational "
                "updates, completed work, blockers, "
                "and employee responses?"
            ),
        )

        personal_context = extract_recall_text(
            personal_recall_resp
        )

    except Exception as e:

        logging.warning(
            "Hindsight personal refresh failed "
            "for '%s': %s",
            employee_id,
            e,
        )

    # ---------------------------------------------------------------
    # Team memory
    # ---------------------------------------------------------------

    try:

        team_recall_resp = _hindsight_recall(
            bank_id="team_ops",
            query=(
                "What are the most recent cross-team "
                "operational updates, completed work, "
                "blockers, and dependencies?"
            ),
        )

        team_context = extract_recall_text(
            team_recall_resp
        )

    except Exception as e:

        logging.warning(
            "Hindsight team_ops refresh failed: %s",
            e,
        )

    return {
        "personal_context": personal_context,
        "team_context": team_context,
    }


# =====================================================================
# MANAGER EXECUTIVE DASHBOARD
# =====================================================================

def generate_manager_dashboard_summary() -> str:
    """
    Step 10:

    Gathers operational context across:

        emp_alice
        emp_bob
        emp_charlie
        team_ops

    using Hindsight reflect with recall fallback,
    then uses Groq for executive synthesis.
    """

    print(
        "\n📊 [Step 10] Gathering operational "
        "context across all memory banks..."
    )

    all_reflections = []

    target_banks = [
        "emp_alice",
        "emp_bob",
        "emp_charlie",
        "team_ops",
    ]

    for bank_id in target_banks:

        if not HINDSIGHT_API_KEY:

            all_reflections.append(
                f"--- Bank: {bank_id} ---\n"
                "No live memory connection available."
            )

            continue

        try:

            reflect_resp = _hindsight_reflect(
                bank_id=bank_id,
                query=(
                    "What are the current operational "
                    "observations, completed milestones, "
                    "and active bottlenecks?"
                ),
            )

            observations = extract_reflect_text(
                reflect_resp
            )

            all_reflections.append(
                f"--- Bank: {bank_id} ---\n"
                f"{observations}"
            )

        except Exception as e:

            logging.warning(
                "Reflect failed for bank '%s': %s",
                bank_id,
                e,
            )

            # -------------------------------------------------------
            # Recall fallback
            # -------------------------------------------------------

            try:

                recall_resp = _hindsight_recall(
                    bank_id=bank_id,
                    query=(
                        "Summary of current operational "
                        "status, completed work, "
                        "and unresolved blockers"
                    ),
                )

                all_reflections.append(
                    f"--- Bank: {bank_id} ---\n"
                    f"{extract_recall_text(recall_resp)}"
                )

            except Exception as recall_error:

                logging.error(
                    "Recall fallback also failed "
                    "for bank '%s': %s",
                    bank_id,
                    recall_error,
                )

                all_reflections.append(
                    f"--- Bank: {bank_id} ---\n"
                    "Unable to retrieve memory."
                )

    combined_reflections = "\n\n".join(
        all_reflections
    )

    # ---------------------------------------------------------------
    # Groq synthesis
    # ---------------------------------------------------------------

    if not groq_client:

        return (
            "### Executive Summary "
            "(Offline Mode)\n\n"
            "Collected Context:\n"
            f"{combined_reflections}"
        )

    print(
        "⚡ Generating Manager Executive "
        "Dashboard via Groq..."
    )

    prompt = f"""
You are an Executive Operations Assistant.

Synthesize the following Hindsight memory context
from the team banks:

emp_alice
emp_bob
emp_charlie
team_ops

into a clean executive status report.

REFLECTED MEMORY DATA:

{combined_reflections}

INSTRUCTIONS:

Focus on:

1. Current progress
2. Completed work
3. Unresolved blockers
4. Dependencies
5. Risks and uncertainties
6. Key team updates
7. Next steps

Do NOT expose raw conversational transcripts
or internal debug details.

FORMAT:

### 🎯 Current Progress & Completed Milestones

### ⚠️ Active Blockers & Dependencies

### 🚀 Release Risks & Next Steps

### 📈 Team Operational Velocity

Keep the report concise and professional.
"""

    try:

        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.2,
        )

        if response and response.choices:

            return (
                response.choices[0]
                .message.content
                .strip()
            )

    except Exception as e:

        logging.error(
            "Groq manager dashboard synthesis "
            "failed: %s",
            e,
        )

    return (
        "### Executive Operations Summary\n\n"
        "*Gathered Memory Context*:\n"
        f"{combined_reflections}"
    )


# =====================================================================
# COMPLETE DEMO FLOW
# =====================================================================

def run_complete_demo():
    """
    Complete command-line demonstration.
    """

    print(
        "=================================================================="
    )

    print(
        "🤖 DAILY OPERATIONS SYNTHESIZER — COMPLETE DEMO FLOW"
    )

    print(
        "=================================================================="
    )

    # ---------------------------------------------------------------
    # Step 1
    # ---------------------------------------------------------------

    print(
        "\n📌 [Step 1] Initializing demo with existing "
        "Days 1–9 seeded Hindsight memories."
    )

    print(
        " Memory Banks Active: "
        "'emp_alice', 'emp_bob', "
        "'emp_charlie', 'team_ops'"
    )

    target_emp = "emp_alice"

    # ---------------------------------------------------------------
    # Steps 2–6
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Step 7
    # ---------------------------------------------------------------

    simulated_user_reply = (
        "Yep, pushed to staging."
    )

    print(
        f"\n👤 [Step 7] MINIMAL EMPLOYEE RESPONSE "
        f"RECEIVED: \"{simulated_user_reply}\""
    )

    # ---------------------------------------------------------------
    # Steps 8–9
    # ---------------------------------------------------------------

    process_result = process_employee_response(
        employee_id=target_emp,
        user_response=simulated_user_reply,
        question_asked=checkin_data[
            "proactive_question"
        ],
    )

    print(
        f"💡 [Step 8] FACTUAL INTERPRETATION: "
        f"{process_result['factual_update']}"
    )

    print(
        f"✅ {process_result['message']}"
    )

    # ---------------------------------------------------------------
    # Step 10
    # ---------------------------------------------------------------

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

    print(
        dashboard_report
    )

    print(
        "\n=================================================================="
    )


# =====================================================================
# CLEANUP
# =====================================================================

def close_clients():
    """
    Close the Groq client.

    Hindsight clients are created and closed inside each isolated
    async operation, so there is no persistent Hindsight session
    to close here.
    """

    global groq_client

    if groq_client is not None:

        try:
            groq_client.close()

        except Exception:
            pass

        groq_client = None


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":

    try:
        run_complete_demo()

    finally:
        close_clients()