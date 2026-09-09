"""PDF export for a single session.

One function: build_session_report(). Kept in its own file the way ai.py and
db.py are — one concern per module. Renders whatever a session already has
(summary, tasks, facts, transcript); it reads stored data and runs no AI
call of its own, so it's just a formatting layer on top of Milestone 4/5's
output, not a new source of memory.

Uses reportlab: pure-Python, no system libraries to install (WeasyPrint,
by contrast, needs Pango/Cairo — a real ask on Render's build image and on
a teammate's Windows machine, for a prototype that needs one plain report).
"""

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

# Same palette as index.css's light tokens (--accent, --text, --text-faint,
# --task, --fact) — a PDF pulled from the app should look like it came from
# the app, not from a generic report template.
ACCENT = colors.HexColor("#a35a00")
TEXT = colors.HexColor("#1d1d1f")
MUTED = colors.HexColor("#57575d")
FAINT = colors.HexColor("#86868b")
TASK = colors.HexColor("#16704a")
FACT = colors.HexColor("#29527a")
RULE = colors.HexColor("#e3e3e8")

_styles = getSampleStyleSheet()

_STYLE_EYEBROW = ParagraphStyle(
    "Eyebrow", parent=_styles["Normal"], fontName="Helvetica", fontSize=8.5,
    textColor=FAINT, tracking=0, spaceAfter=2,
)
_STYLE_TITLE = ParagraphStyle(
    "ReportTitle", parent=_styles["Title"], fontName="Helvetica-Bold", fontSize=22,
    textColor=TEXT, alignment=TA_LEFT, spaceAfter=0, leading=26,
)
_STYLE_META = ParagraphStyle(
    "Meta", parent=_styles["Normal"], fontName="Helvetica", fontSize=9,
    textColor=FAINT, spaceBefore=4, spaceAfter=0,
)
_STYLE_H2 = ParagraphStyle(
    "H2", parent=_styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5,
    textColor=TEXT, spaceBefore=18, spaceAfter=8,
)
_STYLE_BODY = ParagraphStyle(
    "Body", parent=_styles["Normal"], fontName="Helvetica", fontSize=10.5,
    textColor=TEXT, leading=16,
)
_STYLE_HINT = ParagraphStyle(
    "Hint", parent=_styles["Normal"], fontName="Helvetica-Oblique", fontSize=10,
    textColor=FAINT, leading=15,
)
_STYLE_TASK_ITEM = ParagraphStyle("TaskItem", parent=_STYLE_BODY, textColor=TEXT)
_STYLE_FACT_ITEM = ParagraphStyle("FactItem", parent=_STYLE_BODY, textColor=TEXT)
_STYLE_TRANSCRIPT = ParagraphStyle(
    "Transcript", parent=_styles["Normal"], fontName="Courier", fontSize=8.5,
    textColor=MUTED, leading=13,
)


def _bullet_list(items: list[str], item_style: ParagraphStyle, bullet_color) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(text, item_style), bulletColor=bullet_color) for text in items],
        bulletType="bullet",
        bulletFontSize=6,
        leftIndent=14,
        spaceBefore=0,
        # Nudge the dot down onto the text's optical centre — at 6pt it
        # otherwise floats up near the cap height of a 10.5pt line.
        bulletOffsetY=-3,
    )


def _escape(text: str) -> str:
    """Paragraph text is a tiny HTML subset — a raw '&' or '<' from a
    transcript would otherwise break layout or silently swallow text."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Display order and colour family for the six memory categories — kept in
# step with frontend/src/components/Memory.jsx so the PDF and the app group
# and colour the same way. Actionable kinds take the task colour, settled/
# known kinds the fact colour.
_CATEGORY_ORDER = ["Action Item", "Task", "Decision", "Requirement", "Preference", "Fact"]
_ACTIONABLE = {"Action Item", "Task"}

_STYLE_MEMORY_ITEM = ParagraphStyle(
    "MemoryItem", parent=_STYLE_BODY, leftIndent=14, spaceAfter=3,
)


def _append_memory(story: list, memory: list) -> None:
    """Renders typed memory objects grouped by category. Each surviving item
    is a `<category> — <text>` line, the category tag coloured by family, so
    a glance shows the six-way structure the product is built on."""
    valid = {c: [] for c in _CATEGORY_ORDER}
    for obj in memory:
        if not isinstance(obj, dict):
            continue
        category = (obj.get("category") or "").strip()
        text = (obj.get("text") or "").strip()
        if category in valid and text:
            valid[category].append(text)

    for category in _CATEGORY_ORDER:
        items = valid[category]
        if not items:
            continue
        colour = TASK if category in _ACTIONABLE else FACT
        tag = colour.hexval()[2:]  # 0x... -> rrggbb for the <font> tag
        for text in items:
            story.append(
                Paragraph(
                    f'<font color="#{tag}"><b>{_escape(category)}</b></font> &nbsp; {_escape(text)}',
                    _STYLE_MEMORY_ITEM,
                )
            )


def build_session_report(session: dict) -> bytes:
    """session: {id, timestamp, summary, facts, tasks, transcript} — the
    same shape GET /sessions/{id} returns. Returns PDF bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title="Second Coworker — Session Report",
    )

    when = session.get("timestamp") or ""
    try:
        # Built without strftime's %-d / %-I (which strip leading zeros but
        # are glibc-only — they raise on Windows, so the report would read
        # differently on a teammate's laptop than on Render's Linux build).
        dt = datetime.fromisoformat(when.replace("Z", "+00:00"))
        hour12 = dt.hour % 12 or 12
        when_label = (
            f"{dt:%A, %B} {dt.day}, {dt.year} · "
            f"{hour12}:{dt.minute:02d} {dt:%p} UTC"
        )
    except ValueError:
        when_label = when

    story = [
        Paragraph("SECOND COWORKER · SESSION REPORT", _STYLE_EYEBROW),
        Paragraph("Meeting Report", _STYLE_TITLE),
        Paragraph(_escape(when_label), _STYLE_META),
        Spacer(1, 14),
        HRFlowable(width="100%", thickness=1, color=RULE, spaceAfter=2),
    ]

    summary = (session.get("summary") or "").strip()
    story.append(Paragraph("SUMMARY", _STYLE_H2))
    if summary:
        # The model's summary is plain text (per CLAUDE.md's contract), but
        # it can span multiple paragraphs — split on blank lines rather than
        # forcing the whole thing into one Paragraph, which loses breaks.
        for para in summary.split("\n\n"):
            para = para.strip()
            if para:
                story.append(Paragraph(_escape(para), _STYLE_BODY))
                story.append(Spacer(1, 6))
    else:
        story.append(Paragraph(
            "No summary was generated for this session — extraction either failed or never ran.",
            _STYLE_HINT,
        ))

    # When the session carries typed memory, the report leads with it — the
    # categories are the point — and skips the flat tasks/facts sections,
    # exactly as the Review screen does. Older sessions (and pre-migration
    # projects) have no memory array, so they fall back to tasks/facts.
    memory = session.get("memory") or []
    if memory:
        story.append(Paragraph(f"STRUCTURED MEMORY ({len(memory)})", _STYLE_H2))
        _append_memory(story, memory)
    else:
        tasks = session.get("tasks") or []
        story.append(Paragraph(f"TASKS ({len(tasks)})", _STYLE_H2))
        if tasks:
            story.append(_bullet_list([_escape(t) for t in tasks], _STYLE_TASK_ITEM, TASK))
        else:
            story.append(Paragraph("None extracted.", _STYLE_HINT))

        facts = session.get("facts") or []
        story.append(Paragraph(f"KEY FACTS ({len(facts)})", _STYLE_H2))
        if facts:
            story.append(_bullet_list([_escape(f) for f in facts], _STYLE_FACT_ITEM, FACT))
        else:
            story.append(Paragraph("None extracted.", _STYLE_HINT))

    transcript = (session.get("transcript") or "").strip()
    story.append(Paragraph("RAW TRANSCRIPT", _STYLE_H2))
    if transcript:
        # Courier at small size, one Paragraph per line so long meetings
        # paginate instead of overflowing a single unbreakable block.
        for line in transcript.splitlines():
            story.append(Paragraph(_escape(line) or "&nbsp;", _STYLE_TRANSCRIPT))
    else:
        story.append(Paragraph("(empty — no speech captured)", _STYLE_HINT))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE))
    story.append(Spacer(1, 6))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(
        f"Session {session.get('id', '')} · generated {generated}", _STYLE_META,
    ))

    doc.build(story)
    return buf.getvalue()
