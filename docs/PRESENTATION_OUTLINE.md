# Technical Presentation Outline: Agentic Conversational AI System

## Slide 1: Title Slide
* **Title**: Agentic Conversational AI System for E-commerce Support
* **Subtitle**: A production-ready RAG-based assistant with deterministic workflows
* **Author**: Nguyễn Trọng Minh
* **Date**: April 2026

## Slide 2: Problem Statement
* **Challenge**: Traditional chatbots are either too rigid (rule-based) or too unpredictable (pure LLM).
* **Requirement**: Need for a system that can answer complex queries from documents (RAG) while maintaining strict control over business processes (Order Status).
* **Security**: Handling sensitive data (SSN) requires deterministic state management.

## Slide 3: Solution Architecture
* **Overview**: FastAPI backend with a hybrid routing approach.
* **Core Components**:
    * **Intent Router**: Classifies user intent into RAG, Tool Workflow, or Fallback.
    * **RAG Pipeline**: Document ingestion, vector storage (Chroma), and semantic retrieval.
    * **Deterministic Workflow**: State machine for multi-turn data collection and validation.

## Slide 4: Retrieval-Augmented Generation (RAG)
* **Pipeline**: PDF Document → Recursive Character Splitting → HuggingFace Embeddings → ChromaDB.
* **Retrieval**: Semantic similarity search with context window optimization.
* **Generation**: Streaming responses via OpenRouter (LLM) for better UX.

## Slide 5: Deterministic Tool Workflows
* **Design Decision**: Why NOT use autonomous agents?
* **State Machine**: Step-by-step slot collection (Name, SSN, DOB).
* **Validation**: Built-in validation for sensitive formats (SSN, Date).
* **Reliability**: Zero hallucination risk for critical business logic.

## Slide 6: Observability & Data Strategy (Planned)
* **Structured Logging**: JSON logs are implemented and ready for analysis.
* **Persistence**: SQLite database stores session history and telemetry.
* **Metrics**: Currently tracking latency, token usage, and tool success rates.
* **Data Explorer**: Streamlit dashboard provides basic introspection.
* **Full Monitoring Stack**: Prometheus, Grafana, and Loki are planned future enhancements (not yet deployed).

## Slide 7: Engineering Best Practices
* **Dockerized**: Simplified deployment and environment parity.
* **Security**: Environment variable isolation for secrets.
* **Documentation**: Comprehensive guides for IaC, testing, and system architecture.

## Slide 8: Future Extensions (Level 200/300)
* **Scaling**: Migration to PostgreSQL and Redis.
* **Advanced NLP**: LLM-based intent classification refinement.
* **Monitoring**: Full Prometheus/Grafana stack integration.

## Slide 9: Conclusion & Q&A
* **Summary**: A balanced approach to AI systems combining LLM flexibility with engineering control.
* **Link**: [GitHub Repository Link]
