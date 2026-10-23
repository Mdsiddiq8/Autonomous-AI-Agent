# Autonomous AI Agent

An autonomous AI agent that takes a natural-language request and produces a polished Word document through a multi-step **Plan → Execute → Reflect → Generate** pipeline.

Built as part of the **Fluid AI - Python AI Engineer (Autonomous Agents)** assignment.

---

## Architecture

```
User Request
     │
     ▼
┌─────────────┐
│   Planner   │  Analyzes the request, determines document type,
│  (LLM Call) │  and creates an ordered task list (4-8 tasks)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Executor   │  Executes each task sequentially, generating
│  (LLM Call) │  professional content for each document section
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Reflector  │  Reviews all sections for quality, completeness,
│  (LLM Call) │  and consistency; triggers revisions if needed
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Document Builder  │  Assembles everything into a formatted
│   (python-docx)   │  Word document with title page, TOC, and QA notes
└───────────────────┘
```

### Engineering Improvement: Multi-Step Planning with Reflection/Self-Check

The agent doesn't just generate content in a single pass. It:

1. **Plans** by breaking the request into discrete, ordered tasks
2. **Executes** each task with full context of prior sections for coherence
3. **Reflects** on the output quality (scoring 1-10) and identifies weak sections
4. **Revises** any sections flagged as `needs_revision` with targeted instructions
5. **Generates** the final document only after quality assurance passes

This reflection loop catches gaps, inconsistencies, and quality issues that a single-shot approach would miss — especially on ambiguous or conflicting requests.

---

## Project Structure

```
├── main.py                  # FastAPI backend (REST API)
├── app.py                   # Streamlit frontend (interactive UI)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py      # Coordinates the full pipeline
│   ├── planner.py           # LLM-based task planning
│   ├── executor.py          # LLM-based content generation
│   ├── reflector.py         # LLM-based quality review & revision
│   ├── llm_client.py        # OpenAI API wrapper (chat + JSON mode)
│   └── document_builder.py  # Word document generation (python-docx)
└── outputs/                 # Generated .docx files (gitignored)
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- An OpenAI API key

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Mdsiddiq8/Autonomous-AI-Agent.git
cd Autonomous-AI-Agent

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key
```

---

## Running the Application

### Option 1: Streamlit UI (Recommended)

```bash
streamlit run app.py
```

Opens an interactive web interface where you can:
- Enter a natural-language request
- Watch each pipeline phase execute in real-time
- See the quality score and reflection feedback
- Download the generated Word document

### Option 2: FastAPI REST API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints:**

| Method | Endpoint  | Description                        |
|--------|-----------|------------------------------------|
| GET    | `/`       | Service info and available endpoints |
| GET    | `/health` | Health check                       |
| POST   | `/agent`  | Submit a request for processing    |

**Example API call:**

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"request": "Create a Q4 marketing strategy for a B2B SaaS startup targeting enterprise clients"}'
```

The response includes the execution plan, task results, reflection scores, and the generated document as a base64-encoded `.docx` file.

---

## How It Handles Ambiguity

When faced with vague or conflicting requests, the agent:

- Makes **reasonable professional assumptions** (documented in the output)
- The **Reflector** identifies assumptions made and lists them in the QA notes
- Conflicting requirements are acknowledged and resolved with a best-effort approach
- All assumptions appear both in the API response and in the generated document

**Example ambiguous request:**
> "We need some kind of document for the new project. It involves AI and healthcare but we're not sure about the scope yet. The budget might be between 50K and 500K."

The agent will plan a structured document, note its assumptions about scope and budget, and flag them for human review.

---

## Tech Stack

| Component       | Technology         |
|-----------------|--------------------|
| LLM             | OpenAI GPT-4o-mini |
| Backend API     | FastAPI            |
| Frontend UI     | Streamlit          |
| Document Gen    | python-docx        |
| Validation      | Pydantic v2        |

---

## Sample Output

The agent produces Word documents with:

- Professional title page with document type and date
- Auto-generated table of contents
- 4-8 content sections based on the planned task list
- Quality assurance notes with reflection score
- List of assumptions made (for ambiguous requests)

---

## API Response Schema

```json
{
  "status": "success",
  "request": "original user request",
  "plan": {
    "document_type": "proposal",
    "document_title": "...",
    "summary": "..."
  },
  "task_list": [
    {"id": 1, "title": "...", "status": "completed"}
  ],
  "execution_results": [
    {
      "task_id": 1,
      "task_title": "...",
      "section_heading": "...",
      "content_length": 350,
      "revised": false
    }
  ],
  "reflection": {
    "overall_quality": "good",
    "score": 8,
    "feedback": "...",
    "assumptions_made": ["..."]
  },
  "document": {
    "filename": "Document_Title_20261022_183615.docx",
    "base64": "..."
  },
  "execution_log": [...]
}
```
