"""Seeds a connected story of prior sessions so recall has something to weave.

Why this exists: CLAUDE.md's demo script asks "What did I decide in
yesterday's meeting?" — but every session created during development is
timestamped today, so the model answers from a *today* meeting without
flagging the date mismatch and the headline demo moment goes quietly wrong.

Beyond that one question, the product's whole bet is *cross-session*
structured memory — so one seeded meeting undersells it. This seeds three
dated sessions that share a storyline (the "Acme" launch): a kickoff, a
design review, and a pre-signing check-in. That lets recall do the thing
competitors can't — answer a question by connecting several meetings:

  "What did we decide about the launch?"   -> spans the design review
  "What does the client want?"             -> kickoff + pre-signing
  "What's still outstanding?"              -> open tasks across all three

Each row is fully formed (transcript + summary + facts + tasks) and
backdated, so the demo is reproducible and deterministic.

Run from backend/:  python seed_demo.py
Add --reset to delete any previously seeded demo sessions first, so
re-running before a rehearsal doesn't stack duplicates.
"""

import sys
from datetime import datetime, timedelta, timezone

from db import get_client

# Marker kept inside each seeded transcript so the rows are identifiable for
# --reset without needing an extra schema column.
SEED_MARKER = "[seeded-demo-session]"


# Each session: how many days back it happened, plus its fully-formed memory.
# Ordered oldest-first so the storyline reads forward; the launch decision in
# the design review references the timeline set at kickoff, and the
# pre-signing meeting references both.
SESSIONS = [
    {
        "days_ago": 6,
        "transcript": (
            f"{SEED_MARKER} Kickoff with Acme. Let's set the scope. They want the "
            "customer portal rebuilt, and the budget they signed off is forty "
            "thousand. The target we're aiming for is a launch in February. "
            "They were clear the portal has to support single sign-on from day "
            "one, that's a hard requirement on their side. Hey Coworker, remind "
            "me to send them the project plan."
        ),
        "summary": (
            "Kickoff meeting with the client Acme to scope the customer portal "
            "rebuild. The signed-off budget is $40,000 and the initial launch "
            "target is February. Acme set single sign-on as a hard requirement "
            "from launch. A reminder was captured to send Acme the project plan."
        ),
        "facts": [
            "Budget for the Acme portal rebuild is $40,000",
            "Initial launch target is February",
            "Single sign-on is a hard requirement from launch",
        ],
        "tasks": ["Send Acme the project plan"],
    },
    {
        "days_ago": 3,
        "transcript": (
            f"{SEED_MARKER} Design review for the Acme portal. The design work "
            "isn't going to be ready for February, so we decided to push the "
            "launch to March. Marketing asked for weekly check-ins instead of "
            "the daily standups and we agreed that works better for everyone. "
            "Also the client mentioned they'd prefer the portal in their brand "
            "colours, not our default theme. Hey Coworker, remind me to update "
            "the timeline in the shared doc."
        ),
        "summary": (
            "Design review for the Acme portal. Because the design work would "
            "not be ready for February, the team decided to push the launch to "
            "March. They agreed to switch from daily standups to weekly "
            "check-ins at marketing's request. The client also stated a "
            "preference for the portal in their own brand colours rather than "
            "the default theme."
        ),
        "facts": [
            "Decided to push the launch from February to March",
            "Design work would not be ready for February",
            "Agreed to switch from daily standups to weekly check-ins",
            "Client prefers the portal in their own brand colours over the default theme",
        ],
        "tasks": ["Update the timeline in the shared doc"],
    },
    {
        "days_ago": 1,
        "transcript": (
            f"{SEED_MARKER} Quick check-in before we send the contract. The "
            "client wants to see the final numbers before they sign anything, "
            "so nothing goes out until they've reviewed the costs. We're still "
            "on track for the March launch. Hey Coworker, remind me to send the "
            "updated deck to the client."
        ),
        "summary": (
            "Short pre-signing check-in on the Acme engagement. The client "
            "requires the final numbers before signing the contract, so nothing "
            "is sent until they review the costs. The March launch is still on "
            "track. A reminder was captured to send the updated deck to the "
            "client."
        ),
        "facts": [
            "Client requires final numbers before signing the contract",
            "March launch is still on track",
        ],
        "tasks": ["Send the updated deck to the client"],
    },
]


def reset(client):
    rows = client.table("sessions").select("id,transcript").execute()
    seeded = [r["id"] for r in rows.data if SEED_MARKER in (r["transcript"] or "")]
    for sid in seeded:
        # tasks cascade on session delete (see database/schema.sql)
        client.table("sessions").delete().eq("id", sid).execute()
    return len(seeded)


def main():
    client = get_client()

    if "--reset" in sys.argv:
        removed = reset(client)
        print(f"Removed {removed} previously seeded session(s).")

    now = datetime.now(timezone.utc)
    for spec in SESSIONS:
        when = now - timedelta(days=spec["days_ago"])
        session = (
            client.table("sessions")
            .insert(
                {
                    "transcript": spec["transcript"],
                    "summary": spec["summary"],
                    "facts": spec["facts"],
                    "timestamp": when.isoformat(),
                }
            )
            .execute()
        )
        session_id = session.data[0]["id"]
        if spec["tasks"]:
            client.table("tasks").insert(
                [
                    {"session_id": session_id, "text": t, "timestamp": when.isoformat()}
                    for t in spec["tasks"]
                ]
            ).execute()
        print(f"Seeded session {session_id} dated {when.date()} ({spec['days_ago']}d ago).")

    print()
    print("Story seeded. Try in Recall:")
    print('  "What did we decide about the launch?"')
    print('  "What does the client want?"')
    print('  "What is still outstanding?"')


if __name__ == "__main__":
    main()
