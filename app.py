from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import anthropic
import json
import re
import os
import requests
from datetime import datetime

client = anthropic.Anthropic()

# ── Airtable config ──────────────────────────────────────────
AIRTABLE_TOKEN   = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE   = os.getenv("AIRTABLE_TABLE", "Feedback")
AIRTABLE_URL     = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

client = anthropic.Anthropic()

st.set_page_config(
    page_title="Hubble Feedback Processor",
    layout="wide"
)

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .stApp { background: #f8f9fb; }

    .top-header {
        background: #0f0f0e;
        color: white;
        padding: 20px 32px;
        margin: -1rem -1rem 2rem -1rem;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .logo {
        width: 36px; height: 36px;
        background: #e8a020;
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 14px; color: #0f0f0e;
    }
    .brand { font-size: 1rem; font-weight: 600; }
    .brand-sub { font-size: 0.72rem; color: rgba(255,255,255,0.5); margin-top: 2px; }

    .card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 24px;
        margin-bottom: 16px;
    }
    .card-title {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 12px;
    }

    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .badge-revision  { background: #fef3c7; color: #92400e; }
    .badge-approval  { background: #dcfce7; color: #14532d; }
    .badge-brief     { background: #ede9fe; color: #4c1d95; }
    .badge-question  { background: #dbeafe; color: #1e3a8a; }
    .badge-high      { background: #fee2e2; color: #7f1d1d; }
    .badge-medium    { background: #fef9c3; color: #854d0e; }
    .badge-low       { background: #dcfce7; color: #14532d; }

    .field-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    .field-value {
        font-size: 0.92rem;
        font-weight: 500;
        color: #0f172a;
        margin-bottom: 16px;
    }
    .highlight-box {
        background: #f8faff;
        border-left: 3px solid #2563eb;
        border-radius: 0 6px 6px 0;
        padding: 12px 16px;
        font-size: 0.88rem;
        color: #1e3a8a;
        line-height: 1.7;
        margin-bottom: 12px;
    }
    .reply-box {
        background: #f0fdf4;
        border-left: 3px solid #16a34a;
        border-radius: 0 6px 6px 0;
        padding: 12px 16px;
        font-size: 0.88rem;
        color: #14532d;
        line-height: 1.7;
        font-style: italic;
    }
    .whatsapp-bubble {
        background: #dcfce7;
        border-radius: 12px 12px 12px 2px;
        padding: 12px 16px;
        font-size: 0.9rem;
        color: #14532d;
        line-height: 1.6;
        max-width: 85%;
        margin-bottom: 8px;
    }
    .whatsapp-time {
        font-size: 0.68rem;
        color: #94a3b8;
        margin-bottom: 16px;
    }
    .stTextArea textarea {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        font-size: 0.92rem !important;
        line-height: 1.6 !important;
        padding: 12px 16px !important;
    }
    .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    }
    .stButton > button {
        background: #0f0f0e !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: #1a1a18 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    .stSelectbox > div > div {
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
    }
    [data-testid="metric-container"] {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="top-header">
    <div class="logo">H</div>
    <div>
        <div class="brand">Hubble Collective</div>
        <div class="brand-sub">AI Feedback Processor</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Claude processing ────────────────────────────────────────
def process_feedback(feedback: str, project_name: str, client_name: str) -> dict:
    prompt = f"""
You are an AI operations assistant for Hubble Collective, a creative agency.
Your job is to process raw client feedback from WhatsApp and convert it into
a structured brief for the team.

Hubble's aesthetic principles:
- Authentic storytelling over corporate polish
- Warm, human-centered visual style
- Playful but purposeful design
- Emotional resonance over technical perfection
- Brand voice: conversational, confident, creative

Client: {client_name}
Project: {project_name}
Raw feedback: {feedback}

Analyze this feedback and return ONLY a JSON object with these exact fields:
{{
    "category": "Revision Request|Approval|New Brief|Question",
    "priority": "High|Medium|Low",
    "assigned_to": ["Editor"|"Designer"|"PM"|"Founder"],
    "issues_identified": ["issue 1", "issue 2"],
    "action_items": ["action 1", "action 2"],
    "aesthetic_notes": "any notes about brand/aesthetic alignment",
    "estimated_turnaround": "e.g. 1 day|2 days|Same day",
    "requires_founder_review": true|false,
    "founder_review_reason": "reason if true, else null",
    "feedback_summary": "2-sentence summary for the team",
    "client_reply": "Professional but warm WhatsApp reply to send client. 
                     2-3 sentences max. Acknowledge, confirm action, give timeline."
}}

Return ONLY the JSON. No explanation.
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)

def log_to_airtable(feedback: str, client_name: str,
                     project: str, result: dict) -> bool:
    """Log processed feedback to Airtable."""
    assigned = result.get("assigned_to", [])
    actions  = result.get("action_items", [])

    payload = {
        "fields": {
            "Client Name":       client_name,
            "Project":           project,
            "Category":          result.get("category", ""),
            "Priority":          result.get("priority", ""),
            "Assigned To":       ", ".join(assigned),
            "Summary":           result.get("feedback_summary", ""),
            "Action Items":      "\n".join([f"• {a}" for a in actions]),
            "Aesthetic Notes":   result.get("aesthetic_notes", ""),
            "Client Reply":      result.get("client_reply", ""),
            "Requires Founder":  result.get("requires_founder_review", False),
            "Turnaround":        result.get("estimated_turnaround", ""),
            "Received At":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Raw Feedback":      feedback
        }
    }

    try:
        response = requests.post(
            AIRTABLE_URL,
            headers=AIRTABLE_HEADERS,
            json=payload
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Airtable error: {e}")
        return False

# ── Session state ────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "feedback_text" not in st.session_state:
    st.session_state.feedback_text = None
if "airtable_logged" not in st.session_state:
    st.session_state.airtable_logged = None


# ── Layout ───────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.2])

# ── LEFT: Input ──────────────────────────────────────────────
with col_left:
    st.markdown("""
    <div style="font-size:1.2rem; font-weight:700; color:#0f172a; margin-bottom:4px;">
        Process Client Feedback
    </div>
    <div style="font-size:0.85rem; color:#64748b; margin-bottom:20px;">
        Paste raw WhatsApp feedback — Claude structures it instantly
    </div>
    """, unsafe_allow_html=True)

    client_name = st.text_input("Client Name", placeholder="e.g. Bloom Studio")
    project_name = st.text_input("Project Name", placeholder="e.g. Brand Campaign Q3")

    # Sample feedbacks
    st.markdown("""
    <div style="font-size:0.72rem; font-weight:600; letter-spacing:0.1em;
                text-transform:uppercase; color:#94a3b8; margin:16px 0 8px;">
        Try a sample
    </div>
    """, unsafe_allow_html=True)

    sample = st.selectbox(
        "Load sample feedback",
        [
            "— select —",
            "Logo feels too corporate",
            "Love the direction, minor tweaks",
            "Animation timing is off",
            "What's the delivery date?"
        ],
        label_visibility="collapsed"
    )

    samples = {
        "Logo feels too corporate": "Hey! So we looked at the latest draft and honestly the logo feels way too corporate and stiff. We wanted something more playful and approachable — kind of like what we discussed in the first brief. Also the color palette feels a bit cold. Can we warm it up? Maybe more earthy tones? The typography is nice though, keep that.",
        "Love the direction, minor tweaks": "Hi! Overall we love the direction, it's really coming together. Just a few small things — the hero image on slide 3 feels a bit stock-photo-ish, can we use something more authentic? And the tagline could be punchier. Everything else looks great, almost there!",
        "Animation timing is off": "The video looks amazing but the animation timing feels rushed in the middle section around 0:45-1:10. The text is appearing too fast and viewers won't have time to read it. Can the editor slow that down? Also the music cut at the end is a bit abrupt.",
        "What's the delivery date?": "Hi just checking — when can we expect the final files? We have a board presentation on Friday and need everything by Thursday EOD at the latest. Is that doable?"
    }

    feedback_input = st.text_area(
        "Client Feedback",
        value=samples.get(sample, ""),
        height=200,
        placeholder="Paste WhatsApp message here...",
        label_visibility="collapsed"
    )

    process_btn = st.button("Process Feedback →")

    if process_btn:
        if not feedback_input.strip():
            st.error("Please enter some feedback to process.")
        elif not client_name.strip():
            st.error("Please enter the client name.")
        elif not project_name.strip():
            st.error("Please enter the project name.")
        else:
            with st.spinner("Claude is processing..."):
                try:
                    result = process_feedback(
                        feedback_input,
                        project_name,
                        client_name
                    )
                    st.session_state.result = result
                    st.session_state.feedback_text = feedback_input

                    # Log to Airtable
                    logged = log_to_airtable(
                        feedback_input,
                        client_name,
                        project_name,
                        result
                    )
                    st.session_state.airtable_logged = logged

                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Show WhatsApp bubble preview
    if st.session_state.feedback_text:
        st.markdown("""
        <div style="font-size:0.72rem; font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#94a3b8; margin:20px 0 8px;">
            Original Message
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="whatsapp-bubble">{st.session_state.feedback_text}</div>
        <div class="whatsapp-time">via WhatsApp</div>
        """, unsafe_allow_html=True)


# ── RIGHT: Output ────────────────────────────────────────────
with col_right:
    if st.session_state.result:
        r = st.session_state.result

        st.markdown("""
        <div style="font-size:1.2rem; font-weight:700; color:#0f172a; margin-bottom:4px;">
            Structured Brief
        </div>
        <div style="font-size:0.85rem; color:#64748b; margin-bottom:20px;">
            Auto-generated — ready to share with the team
        </div>
        """, unsafe_allow_html=True)

        # Top metrics
        cat = r.get("category", "")
        pri = r.get("priority", "")
        cat_class = {
            "Revision Request": "revision",
            "Approval": "approval",
            "New Brief": "brief",
            "Question": "question"
        }.get(cat, "revision")
        pri_class = pri.lower()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="text-align:center; background:white; border:1px solid #e2e8f0;
                        border-radius:8px; padding:16px;">
                <div class="field-label">Category</div>
                <span class="badge badge-{cat_class}">{cat}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="text-align:center; background:white; border:1px solid #e2e8f0;
                        border-radius:8px; padding:16px;">
                <div class="field-label">Priority</div>
                <span class="badge badge-{pri_class}">{pri}</span>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            turnaround = r.get("estimated_turnaround", "TBD")
            st.markdown(f"""
            <div style="text-align:center; background:white; border:1px solid #e2e8f0;
                        border-radius:8px; padding:16px;">
                <div class="field-label">Turnaround</div>
                <div style="font-size:0.92rem; font-weight:600;
                            color:#0f172a;">{turnaround}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Summary
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Summary for Team</div>
            <div class="highlight-box">{r.get('feedback_summary', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Two columns for details
        c1, c2 = st.columns(2)
        with c1:
            # Assigned to
            assigned = r.get("assigned_to", [])
            assigned_str = " · ".join(assigned)
            # Build issues HTML separately
            issues_html = "".join([
                f'<div style="font-size:0.85rem; color:#475569; '
                f'padding:4px 0; border-bottom:1px solid #f1f5f9;">'
                f'• {i}</div>'
                for i in r.get('issues_identified', [])
            ])

            st.markdown(f"""
            <div class="card">
                <div class="card-title">Assigned To</div>
                <div class="field-value">{assigned_str}</div>
                <div class="field-label">Issues Identified</div>
                {issues_html}
            </div>
            """, unsafe_allow_html=True)

        with c2:
            # Action items
            st.markdown(f"""
            <div class="card">
                <div class="card-title">Action Items</div>
                {"".join([f'<div style="font-size:0.85rem; color:#475569; padding:4px 0; border-bottom:1px solid #f1f5f9;">✓ {a}</div>' for a in r.get('action_items', [])])}
            </div>
            """, unsafe_allow_html=True)

        # Aesthetic notes
        if r.get("aesthetic_notes"):
            st.markdown(f"""
            <div class="card">
                <div class="card-title">Aesthetic & Storytelling Notes</div>
                <div class="highlight-box">{r.get('aesthetic_notes')}</div>
            </div>
            """, unsafe_allow_html=True)

        # Founder review
        if r.get("requires_founder_review"):
            st.markdown(f"""
            <div style="background:#fff7ed; border:1px solid #fed7aa;
                        border-left:3px solid #ea580c; border-radius:0 8px 8px 0;
                        padding:14px 18px; margin-bottom:16px;">
                <div style="font-size:0.72rem; font-weight:600; letter-spacing:0.1em;
                            text-transform:uppercase; color:#ea580c; margin-bottom:4px;">
                    Founder Review Required
                </div>
                <div style="font-size:0.85rem; color:#9a3412;">
                    {r.get('founder_review_reason', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Client reply
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Suggested Client Reply (WhatsApp)</div>
            <div class="reply-box">{r.get('client_reply', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Airtable status
        if st.session_state.airtable_logged is True:
            st.success("Logged to Airtable — team notified")
        elif st.session_state.airtable_logged is False:
            st.warning("Airtable logging failed — check credentials")

    else:
        # Empty state
        st.markdown("""
        <div style="background:white; border:1px solid #e2e8f0; border-radius:10px;
                    padding:60px 40px; text-align:center; color:#94a3b8;">
            <div style="font-size:2rem; margin-bottom:12px;">⟶</div>
            <div style="font-size:0.95rem; font-weight:500; margin-bottom:6px;">
                Structured brief appears here
            </div>
            <div style="font-size:0.82rem;">
                Paste feedback on the left and click Process
            </div>
        </div>
        """, unsafe_allow_html=True)