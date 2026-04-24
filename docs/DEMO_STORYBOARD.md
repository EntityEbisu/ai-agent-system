# Project Demo Storyboard & Narration Guide

## Scene 1: Introduction (0:00 - 0:30)
* **Visual**: Streamlit app homepage or terminal running the server.
* **Action**: Introduce yourself and the project goal.
* **Narration**: "Hi, I'm Minh. Today I'll demonstrate my Agentic Conversational AI system, designed for e-commerce customer support. It combines a RAG pipeline with deterministic workflows for a reliable user experience."

## Scene 2: RAG Pipeline in Action (0:30 - 1:30)
* **Visual**: Streamlit Chat Interface.
* **Action**: Type a question like "What are the main risks mentioned in the 10-K report?"
* **Narration**: "First, let's look at the RAG capability. I've ingested a complex 10-K document. The system retrieves relevant chunks and generates a grounded response. Notice the streaming effect, providing immediate feedback to the user."

## Scene 3: Order Status Workflow (1:30 - 3:00)
* **Visual**: Streamlit Chat Interface.
* **Action**: Type "Where is my order?"
* **Narration**: "Now, let's switch to a structured workflow. When I ask about an order, the router identifies the intent and triggers the state machine."
* **Action**: Follow the prompts (Name → SSN → DOB). Enter an invalid SSN once to show error handling.
* **Narration**: "The system asks for specific information step-by-step. It validates my input—for example, catching an incorrect SSN format. Once all data is collected, it executes the mock tool securely."

## Scene 4: Observability & Data Explorer (3:00 - 4:00)
* **Visual**: Streamlit "Data Explorer" tabs.
* **Action**: Click through "Logs", "Sessions", and "Metrics" tabs.
* **Narration**: "Under the hood, we track everything. Here in the Data Explorer, we can see structured JSON logs, session histories, and performance metrics like latency and token usage. This level of observability is crucial for production systems."

## Scene 5: Conclusion (4:00 - 4:30)
* **Visual**: GitHub Repository or Architecture Diagram.
* **Action**: Summarize key takeaways.
* **Narration**: "The system demonstrates a robust architecture that respects both the power of LLMs and the need for engineering control. All code is containerized and ready for deployment. Thanks for watching!"
