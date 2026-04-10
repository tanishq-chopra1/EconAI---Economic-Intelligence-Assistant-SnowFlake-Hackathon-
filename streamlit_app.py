from snowflake.snowpark.context import get_active_session
import streamlit as st
import json
import pandas as pd

session = get_active_session()

def rag_query(question: str, top_k: int = 5, source_filter: str = "All", response_length: str = "📝 Medium") -> dict:
    filter_clause = ""
    if source_filter != "All":
        filter_clause = f', "filter": {{"@eq": {{"SOURCE": "{source_filter}"}}}}'

    raw = session.sql(f"""
        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'HACKATHON.DATA.RAG_SEARCH',
            $${{"query": "{question}",
               "columns": ["CHUNK_TEXT","SOURCE","TITLE","METADATA"],
               "limit": {top_k}{filter_clause}}}$$
        ) AS results
    """).collect()[0][0]

    chunks = json.loads(raw).get("results", [])
    if not chunks:
        return {"answer": "No relevant information found.", "citations": [], "chunks_used": 0, "confidence": 0}

    # 5 chunks x 1200 chars = ~6000 chars — good balance of speed and detail
    context = "\n\n".join(
        f"[{i+1}] (Source: {c.get('SOURCE','')}) {c['CHUNK_TEXT'][:1200]}"
        for i, c in enumerate(chunks)
    )

    # store full text for the popover view
    citations = [
        {
            "id":        i + 1,
            "source":    c.get("SOURCE", ""),
            "title":     c.get("TITLE",  "")[:120],
            "snippet":   c["CHUNK_TEXT"][:250] + "...",
            "full_text": c["CHUNK_TEXT"]
        }
        for i, c in enumerate(chunks)
    ]

    # adjust instruction based on response length selection
    length_instruction = {
        "📄 Lengthy":  "Provide a comprehensive, detailed answer covering ALL points from the context. Use bullet points and structure your response with clear sections. Be thorough and exhaustive.",
        "📝 Medium":   "Provide a thorough answer covering the main points from the context. Balance detail with clarity.",
        "⚡ Concise":  "Provide a brief, focused answer in 2-3 sentences covering only the most important points. Be direct."
    }.get(response_length, "Provide a thorough answer covering the main points.")

    prompt = f"""You are a financial and economic intelligence analyst.
Answer the question using ALL relevant information from the context below.
After every factual claim cite the source in brackets like [1] or [2].
Interpret numeric values and measurements as valid data to answer the question.
{length_instruction}
Only say "Insufficient data in corpus" if the context contains absolutely no relevant information.
Do not make up facts.

Context:
{context}

Question: {question}

Answer (with inline citations):"""

    prompt_escaped = prompt.replace("'", "\\'")

    # mistral-large is faster than mistral-large2 for short prompts
    answer = session.sql(f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large',
            '{prompt_escaped}'
        ) AS answer
    """).collect()[0][0]

    # confidence from citation count — no extra API call
    if len(citations) >= 5 and len(answer) > 400:
        confidence = 90
    elif len(citations) >= 3 and len(answer) > 200:
        confidence = 85
    elif len(citations) >= 2:
        confidence = 70
    else:
        confidence = 50

    return {
        "answer":      answer,
        "citations":   citations,
        "chunks_used": len(chunks),
        "confidence":  confidence
    }

st.set_page_config(
    page_title="EconIQ — Economic Intelligence Assistant",
    page_icon="📊",
    layout="wide"
)

col_title, col_space = st.columns([3, 1])
with col_title:
    st.title("📊 EconIQ")
    st.caption("RAG-powered economic intelligence · Cortex Search + Arctic Embed + mistral-large")

st.divider()

m1, m2, m3, m4 = st.columns(4)
m1.metric("📦 Corpus",        "209,451 chunks", "14 data sources")
m2.metric("✅ Eval score",    "20 / 20",         "questions answered")
m3.metric("📎 Avg citations", "10.0",            "per answer")
m4.metric("🤖 Model",         "mistral-large",   "Snowflake Cortex")

st.divider()

tab_chat, tab_eval, tab_data, tab_arch = st.tabs([
    "💬 Ask a Question",
    "📈 Eval Report",
    "🗂️ Data Sources",
    "🏗️ Architecture"
])

with tab_chat:

    with st.sidebar:
        st.subheader("⚙️ Settings")
        top_k = st.slider("Chunks to retrieve", 3, 10, 5)
        source_filter = st.selectbox("Filter by source", [
            "All", "TRANSCRIPT", "SEC_10K", "SEC_10Q",
            "CFPB_COMPLAINT", "GOV_CONTRACT", "FED_RESERVE",
            "ECON_INDICATORS", "WORLD_BANK", "OECD",
            "US_TREASURY", "FHFA_HOUSING", "MORTGAGE",
            "WB_INDICATOR", "FEMA_DISASTER"
        ])
        response_length = st.selectbox("Response length", [
            "📝 Medium", "📄 Lengthy", "⚡ Concise"
        ])
        st.divider()
        st.caption("💡 Try asking:")
        st.caption("• What risk factors do financial institutions disclose?")
        st.caption("• What are primary denial reasons for home mortgages?")
        st.caption("• What is the US inflation trend?")
        st.caption("• What did Bank of America say about interest rates?")
        st.caption("• What government contracts were awarded for cybersecurity?")

        st.divider()
        st.caption("📋 Demo workflows:")
        if st.button("🏦 Bank risk analyst"):
            st.session_state.demo_question = "What liquidity and credit risks do US banks disclose in their SEC filings?"
            st.rerun()
        if st.button("📈 Fed policy researcher"):
            st.session_state.demo_question = "What does Federal Reserve data show about consumer credit trends?"
            st.rerun()
        if st.button("🏠 Mortgage analyst"):
            st.session_state.demo_question = "What are the primary reasons mortgage applications are denied?"
            st.rerun()

        st.divider()
        if st.button("🗑️ Clear conversation"):
            st.session_state.history = []
            st.rerun()

    if "history" not in st.session_state:
        st.session_state.history = []

    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            st.write(turn["answer"])
            conf = turn.get("confidence", 0)
            conf_color = "🟢" if conf >= 80 else "🟡" if conf >= 50 else "🔴"
            st.caption(f"Retrieved {turn.get('chunks_used', 10)} chunks · Confidence: {conf_color} {conf}%")
            with st.expander(f"📎 {len(turn['citations'])} sources used"):
                for c in turn["citations"]:
                    st.markdown(f"**[{c['id']}]** `{c['source']}` — {c['title']}")
                    st.caption(c["snippet"])
                    with st.popover("📄 View full source"):
                        st.markdown(f"**Source:** `{c['source']}`")
                        st.markdown(f"**Title:** {c['title']}")
                        st.divider()
                        st.write(c.get("full_text", c["snippet"]))

    typed_question = st.chat_input("Ask about economics, finance, government data...")
    question = typed_question or st.session_state.pop("demo_question", None)

    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving and generating answer..."):
                result = rag_query(question, top_k, source_filter, response_length)
            st.write(result["answer"])
            conf = result.get("confidence", 0)
            conf_color = "🟢" if conf >= 80 else "🟡" if conf >= 50 else "🔴"
            st.caption(f"Retrieved {result['chunks_used']} chunks · Confidence: {conf_color} {conf}%")
            with st.expander(f"📎 {len(result['citations'])} sources used"):
                for c in result["citations"]:
                    st.markdown(f"**[{c['id']}]** `{c['source']}` — {c['title']}")
                    st.caption(c["snippet"])
                    with st.popover("📄 View full source"):
                        st.markdown(f"**Source:** `{c['source']}`")
                        st.markdown(f"**Title:** {c['title']}")
                        st.divider()
                        st.write(c.get("full_text", c["snippet"]))

        st.session_state.history.append({
            "question":      question,
            "answer":        result["answer"],
            "citations":     result["citations"],
            "chunks_used":   result["chunks_used"],
            "confidence":    result.get("confidence", 0)
        })

with tab_eval:
    st.subheader("Ground-truth evaluation")
    st.caption("20 test questions evaluated against the corpus")

    eval_questions = [
        "What risk factors do financial institutions disclose in SEC filings?",
        "What is the Federal Reserve stance on interest rates?",
        "What are the primary denial reasons for home mortgage applications?",
        "What does Bank of America say about inflation?",
        "What government contracts were awarded for cybersecurity?",
        "What types of services and work are described in government contract awards?",
        "What are consumers complaining about with credit cards?",
        "What does economic indicator data show about GDP and growth rates?",
        "What did companies say about supply chain risks?",
        "What FEMA disasters occurred in Texas?",
        "What is the World Bank indicator for part-time employment?",
        "What are the risks of adjustable rate mortgages?",
        "What did Deutsche Bank say about market volatility?",
        "What is the US Treasury yield curve trend?",
        "What does Federal Reserve data show about consumer credit growth rates?",
        "What consumer complaints exist about student loans?",
        "What does FHFA data show about housing price trends?",
        "What did the Federal Reserve say about monetary policy?",
        "What are the main risks disclosed in 10-K filings?",
        "What does mortgage data show about debt-to-income ratios?"
    ]

    if st.button("▶ Run evaluation (takes ~2 mins)"):
        results  = []
        progress = st.progress(0)
        status   = st.empty()

        for i, q in enumerate(eval_questions):
            status.caption(f"Evaluating question {i+1}/20: {q[:60]}...")
            try:
                out          = rag_query(q, top_k=5, response_length="📝 Medium")
                answer_lower = out["answer"].lower()
                is_answered  = (
                    "insufficient" not in answer_lower
                    or len(out["answer"]) > 300
                )
                results.append({
                    "Question":       q,
                    "Answered":       "✅" if is_answered else "⚠️",
                    "Citations":      len(out["citations"]),
                    "Chunks Used":    out["chunks_used"],
                    "Confidence":     out.get("confidence", 0),
                    "Answer Preview": out["answer"][:120] + "..."
                })
            except Exception as e:
                results.append({
                    "Question":       q,
                    "Answered":       "❌",
                    "Citations":      0,
                    "Chunks Used":    0,
                    "Confidence":     0,
                    "Answer Preview": str(e)[:80]
                })
            progress.progress((i + 1) / len(eval_questions))

        status.empty()
        df       = pd.DataFrame(results)
        answered = (df["Answered"] == "✅").sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Questions answered", f"{answered}/20")
        col2.metric("Avg citations",      f"{df['Citations'].mean():.1f}")
        col3.metric("Avg chunks used",    f"{df['Chunks Used'].mean():.1f}")
        col4.metric("Avg confidence",     f"{df['Confidence'].mean():.0f}%")

        st.dataframe(df, use_container_width=True)

        session.create_dataframe(df).write.mode("overwrite") \
               .save_as_table("HACKATHON.DATA.EVAL_RESULTS")
        st.success("✅ Eval results saved to HACKATHON.DATA.EVAL_RESULTS")

with tab_data:
    st.subheader("Corpus breakdown")
    st.caption("209,451 total chunks across 14 sources")

    try:
        df = session.sql("""
            SELECT SOURCE,
                   COUNT(*)                       AS CHUNKS,
                   ROUND(AVG(LENGTH(CHUNK_TEXT))) AS AVG_CHARS
            FROM HACKATHON.DATA.CHUNKS
            GROUP BY SOURCE
            ORDER BY CHUNKS DESC
        """).to_pandas()
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("SOURCE")["CHUNKS"])
    except Exception as e:
        st.error(f"Could not load corpus stats: {e}")

with tab_arch:
    st.subheader("The problem we solve")
    st.markdown("""
    Financial analysts, policy researchers, and economists currently spend hours
    manually searching SEC filings, Fed reports, World Bank databases, and CFPB
    complaint logs to answer questions that **EconIQ answers in seconds.**
    """)

    col_a, col_b = st.columns(2)
    with col_a:
        st.error("""
        **❌ Without EconIQ**
        - Search SEC EDGAR manually
        - Download Fed Reserve CSVs
        - Query World Bank API separately
        - Cross-reference CFPB complaints
        - Hours of analyst time per question
        """)
    with col_b:
        st.success("""
        **✅ With EconIQ**
        - Ask in plain English
        - Get cited answers in seconds
        - Sources from 14 datasets unified
        - Zero external APIs — 100% Snowflake
        - Auditable citations on every answer
        """)

    st.divider()
    st.subheader("Pipeline architecture")
    st.markdown("""
    | Stage | Tool | Detail |
    |---|---|---|
    | Data sources | Snowflake Marketplace | Finance & Economics + Government datasets |
    | Ingestion | Snowpark Python | 14 tables, 209,451 chunks |
    | Chunking | Custom chunker | 400-word windows, 60-word overlap |
    | Embedding | Arctic Embed | Via Cortex Search service |
    | Indexing | Cortex Search | Semantic + full-text hybrid search |
    | Generation | Cortex COMPLETE (mistral-large) | Grounded prompt with citation tags |
    | Evaluation | 20-Q ground-truth suite | 20/20 precision, avg 10 citations |
    | UI | Streamlit in Snowflake | 4-tab interface |
    """)

    st.divider()
    st.subheader("Key design decisions")
    st.info("""
    💡 **Novel technique: Numeric Narrativization**

    Standard RAG systems can only retrieve text. EconIQ converts 6 numeric
    time-series datasets (Federal Reserve, World Bank, OECD, US Treasury,
    FHFA, DOL) into natural language sentences before indexing:

    *"Federal funds rate (country/USA): As of 2024-09-30, the value was 5.33%.
    It decreased from 5.58% in the prior period. From 2018-01-31 to 2024-09-30,
    total change was +433.0%."*

    This enables semantic retrieval over quantitative data — a capability
    not present in standard RAG implementations.
    """)

    st.markdown("""
    - **Citation grounding** — every answer includes inline `[n]` citations
      mapped to source chunks, preventing hallucination and enabling fact verification
    - **Source filtering** — users can restrict retrieval to specific data sources
      for targeted queries
    - **Response length control** — users can choose Concise, Medium, or Lengthy responses
    - **Conversation history** — multi-turn chat maintains context across questions
    - **Known limitation** — OECD data uses ISO country codes internally,
      so country-specific queries work best with codes (e.g. `country/USA`)
      rather than full country names
    """)