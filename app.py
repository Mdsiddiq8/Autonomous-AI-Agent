import streamlit as st
import base64
import time
import json
import logging
from agent.orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Autonomous AI Agent",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .task-card {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
    }
    .task-pending {
        border-left-color: #FFC107;
    }
    .task-running {
        border-left-color: #2196F3;
    }
    .reflection-card {
        background: #e8f5e9;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #4CAF50;
    }
    .score-big {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #2e7d32;
    }
    .log-entry {
        font-family: monospace;
        font-size: 0.85rem;
        padding: 0.25rem 0;
        border-bottom: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align:center;'>🤖 Autonomous AI Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Plan → Execute → Reflect → Generate Document</p>", unsafe_allow_html=True)
st.divider()

# Sidebar - Architecture Info
with st.sidebar:
    st.header("About This Agent")
    st.markdown("""
    **How it works:**
    1. **Planner** - Analyzes your request and creates a task list
    2. **Executor** - Writes content for each task step-by-step
    3. **Reflector** - Reviews quality and revises weak sections
    4. **Document Builder** - Generates a polished Word file

    **Engineering Improvement:**
    Multi-step Planning + Reflection/Self-check

    **Tech Stack:**
    - FastAPI + Streamlit
    - OpenAI GPT-4o-mini
    - python-docx
    """)

    st.divider()
    st.subheader("Sample Requests")
    if st.button("📋 Standard Business Request", use_container_width=True):
        st.session_state["sample"] = "Create a Q4 marketing strategy proposal for a B2B SaaS startup targeting enterprise clients"
    if st.button("🧩 Complex / Ambiguous Request", use_container_width=True):
        st.session_state["sample"] = (
            "We need some kind of document for the new project. It involves AI and healthcare "
            "but we're not sure about the scope yet. The budget might be between 50K and 500K. "
            "Some stakeholders want a technical deep-dive while others want a high-level business "
            "overview. The deadline was yesterday but we can probably push it. Also consider "
            "regulatory compliance but don't make it too long."
        )

# Main input
default_text = st.session_state.get("sample", "")
user_request = st.text_area(
    "What document would you like the agent to create?",
    value=default_text,
    height=120,
    placeholder="e.g. Create a project plan for migrating our on-premise infrastructure to AWS cloud...",
)

col_btn, col_spacer = st.columns([1, 3])
with col_btn:
    run_clicked = st.button("🚀 Run Agent", type="primary", use_container_width=True)

if run_clicked and user_request.strip():
    orchestrator = AgentOrchestrator()

    # Phase 1: Planning
    with st.status("🧠 Agent is thinking...", expanded=True) as status:
        st.write("**Phase 1: Planning** - Analyzing your request...")
        try:
            from agent.planner import generate_plan
            plan = generate_plan(user_request)
        except Exception as e:
            st.error(f"Planning failed: {e}")
            st.stop()

        status.update(label="📋 Plan created!", state="running")

    # Show the plan
    st.subheader("📋 Execution Plan")
    plan_col1, plan_col2 = st.columns([2, 1])
    with plan_col1:
        st.markdown(f"**Document:** {plan['document_title']}")
        st.markdown(f"**Type:** {plan['document_type'].replace('_', ' ').title()}")
        st.markdown(f"**Summary:** {plan['summary']}")
    with plan_col2:
        st.metric("Total Tasks", len(plan["tasks"]))

    st.divider()

    # Phase 2: Execution
    st.subheader("⚙️ Task Execution")
    task_containers = {}
    for task in plan["tasks"]:
        task_containers[task["id"]] = st.empty()
        task_containers[task["id"]].info(f"⏳ **Task {task['id']}:** {task['title']}")

    execution_results = []
    document_context = {
        "document_type": plan["document_type"],
        "document_title": plan["document_title"],
    }

    from agent.executor import execute_task
    for task in plan["tasks"]:
        task_containers[task["id"]].warning(f"🔄 **Task {task['id']}:** {task['title']} — Running...")
        try:
            result = execute_task(
                task=task,
                document_context=document_context,
                previous_results=execution_results,
                user_request=user_request,
            )
            execution_results.append(result)
            task_containers[task["id"]].success(
                f"✅ **Task {task['id']}:** {task['title']} — Done ({len(result['content'])} chars)"
            )
        except Exception as e:
            task_containers[task["id"]].error(f"❌ **Task {task['id']}:** {task['title']} — Failed: {e}")

    st.divider()

    # Phase 3: Reflection
    st.subheader("🔍 Quality Review")
    with st.spinner("Reflector agent is reviewing the content..."):
        from agent.reflector import reflect, revise_section
        try:
            reflection = reflect(user_request, document_context, execution_results)
        except Exception as e:
            reflection = {"overall_quality": "unknown", "score": 0, "feedback": f"Reflection failed: {e}"}

    ref_col1, ref_col2, ref_col3 = st.columns(3)
    with ref_col1:
        score = reflection.get("score", 0)
        st.metric("Quality Score", f"{score}/10")
    with ref_col2:
        quality = reflection.get("overall_quality", "unknown")
        emoji = {"excellent": "🌟", "good": "👍", "needs_revision": "🔧"}.get(quality, "❓")
        st.metric("Overall Quality", f"{emoji} {quality.title()}")
    with ref_col3:
        revised_count = 0
        for review in reflection.get("section_reviews", []):
            if review.get("quality") == "needs_revision":
                revised_count += 1
        st.metric("Sections Revised", revised_count)

    st.info(f"**Feedback:** {reflection.get('feedback', 'N/A')}")

    # Phase 4: Revisions
    for review in reflection.get("section_reviews", []):
        if review.get("quality") == "needs_revision" and review.get("revision_instruction"):
            task_id = review["task_id"]
            for result in execution_results:
                if result["task_id"] == task_id:
                    with st.spinner(f"Revising Task {task_id}..."):
                        revised_content = revise_section(
                            section=result,
                            revision_instruction=review["revision_instruction"],
                            document_context=document_context,
                            user_request=user_request,
                        )
                        result["content"] = revised_content
                        result["revised"] = True
                    task_containers[task_id].success(
                        f"🔄 **Task {task_id}:** {result['task_title']} — Revised"
                    )
                    break

    # Show assumptions if any
    assumptions = reflection.get("assumptions_made", [])
    if assumptions:
        with st.expander("🤔 Assumptions Made (for ambiguous requests)"):
            for assumption in assumptions:
                st.markdown(f"- {assumption}")

    st.divider()

    # Phase 5: Document Generation
    st.subheader("📄 Document Generation")
    with st.spinner("Building Word document..."):
        from agent.document_builder import build_document
        filename, doc_base64 = build_document(
            document_title=plan["document_title"],
            document_type=plan["document_type"],
            sections=execution_results,
            reflection=reflection,
        )

    st.success(f"Document generated: **{filename}**")
    doc_bytes = base64.b64decode(doc_base64)
    st.download_button(
        label="📥 Download Word Document",
        data=doc_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True,
    )

    # Expandable: Generated Content Preview
    with st.expander("👁️ Preview Generated Content"):
        for result in execution_results:
            revised_tag = " *(revised)*" if result.get("revised") else ""
            st.markdown(f"### {result['section_heading']}{revised_tag}")
            st.markdown(result["content"])
            st.divider()

elif run_clicked and not user_request.strip():
    st.warning("Please enter a request before running the agent.")
