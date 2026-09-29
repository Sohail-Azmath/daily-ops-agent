import os
import time
from dotenv import load_dotenv
from hindsight_client import Hindsight

# Load environment variables from .env file
load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

if not HINDSIGHT_API_KEY or HINDSIGHT_API_KEY == "your_hindsight_api_key_here":
    raise ValueError(
        "Please set a valid HINDSIGHT_API_KEY in your .env file "
        "before running seed_data.py"
    )

# Initialize Hindsight Client
client = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY
)

print("🚀 Starting Hindsight Memory Seeding (Days 1–9)...\n")


# Synthetic work history for 3 employees across 9 days
SYNTHETIC_HISTORY = [

    # --- DAY 1 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 1",
        "content": "Started Project Alpha PostgreSQL database migration from v13 to v15. Mapped out table schema changes and user auth tables."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 1",
        "content": "Kicked off Project Beta UI redesign in Figma and set up the React component library repo."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 1",
        "content": "Configured Kubernetes cluster staging environment and updated Terraform scripts for AWS deployment."
    },

    # --- DAY 2 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 2",
        "content": "Wrote data migration scripts for User and Org tables on Project Alpha. Ran local test migration successfully with zero data loss."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 2",
        "content": "Built responsive Navbar and Sidebar components for Project Beta. Waiting on backend API schema from Alice for user profile integration."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 2",
        "content": "Upgraded Staging K8s cluster node pool. Identified a network latency bug in the ingress controller."
    },

    # --- DAY 3 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 3",
        "content": "Shared API v2 specs with Bob for Project Beta user profile endpoints. Ran benchmark queries on local Postgres migration, hitting index bottlenecks on the AuditLogs table."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 3",
        "content": "Integrated User Profile UI with Alice's mock API specs on Project Beta. Everything looks clean, waiting on live staging deployment."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 3",
        "content": "Fixed ingress network latency on staging. Started setting up CI/CD pipeline auto-deploys for Project Alpha."
    },

    # --- DAY 4 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 4",
        "content": "Optimized AuditLogs indexes on Project Alpha, reducing query execution time by 65%. Submitted PR #204 for staging deployment review."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 4",
        "content": "Built Dashboard Analytics widgets for Project Beta. Blocked on real metrics API endpoint from Alice."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 4",
        "content": "Reviewed PR #204 for Project Alpha. Noticed missing DB connection pool environment variables for staging setup. Requested Alice to update config."
    },

    # --- DAY 5 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 5",
        "content": "Updated DB connection pool env configs per Charlie's review. Requested Charlie to run the migration script in the staging environment."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 5",
        "content": "Switched focus to Project Beta authentication screens (OAuth2 and SSO integration). Finished Google SSO flow."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 5",
        "content": "Encountered a permission error on staging DB cluster during Project Alpha deployment. Delayed migration by 24 hours to reconfigure AWS IAM roles."
    },

    # --- DAY 6 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 6",
        "content": "Still blocked on Project Alpha staging deployment due to Charlie's AWS IAM role issue. Started drafting metrics API documentation for Bob."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 6",
        "content": "Finished SAML/Okta SSO integration on Project Beta. Conducted self-code review and refactored auth state hooks."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 6",
        "content": "Resolved AWS IAM role permission issues for staging DB cluster. Successfully executed dry-run migration for Project Alpha."
    },

    # --- DAY 7 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 7",
        "content": "Verified dry-run DB migration on staging. 95% complete with Project Alpha backend. Needs Charlie's final sign-off on prod backup policy."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 7",
        "content": "Started mobile responsiveness adjustments for Project Beta UI. Added dark mode toggle support."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 7",
        "content": "Configured automated nightly snapshots for Project Alpha DB. Approved deployment pipeline to staging."
    },

    # --- DAY 8 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 8",
        "content": "Completed staging deployment for Project Alpha backend API v2. Sent live staging endpoints to Bob."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 8",
        "content": "Connected Project Beta UI to Alice's live staging endpoints. Found 1 minor CORS bug on user profile fetch."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 8",
        "content": "Initiated security audit scan on K8s cluster and updated SSL certificates across all subdomains."
    },

    # --- DAY 9 ---
    {
        "bank_id": "emp_alice",
        "day": "Day 9",
        "content": "Fixed CORS configuration on staging API for Bob. DB migration on Project Alpha is 99% finalized, waiting on final QA regression test."
    },
    {
        "bank_id": "emp_bob",
        "day": "Day 9",
        "content": "Verified CORS fix with Alice. Project Beta frontend phase 1 is completely integrated and ready for internal demo."
    },
    {
        "bank_id": "emp_charlie",
        "day": "Day 9",
        "content": "Completed SSL cert renewal and cluster security scan. Ready to support Project Alpha production release tomorrow."
    }
]


def seed_memories():
    total_items = len(SYNTHETIC_HISTORY)

    for index, entry in enumerate(SYNTHETIC_HISTORY, start=1):

        bank_id = entry["bank_id"]
        day = entry["day"]
        content = entry["content"]

        print(
            f"[{index}/{total_items}] "
            f"Retaining memory for '{bank_id}' ({day})..."
        )

        try:
            client.retain(
                bank_id=bank_id,
                content=f"[{day}] {content}"
            )

            # Short delay to respect rate limits
            time.sleep(0.3)

        except Exception as e:
            print(
                f"❌ Error seeding memory for "
                f"{bank_id} on {day}: {e}"
            )

    print(
        "\n✅ Successfully seeded 9 days of "
        "synthetic memories into Hindsight Cloud!"
    )

    print(
        "Memory banks active: "
        "'emp_alice', 'emp_bob', 'emp_charlie'"
    )


if __name__ == "__main__":
    seed_memories()