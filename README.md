# Autonomous Multi-Agent Social Media Automation Platform

A production-grade, AI-driven automation ecosystem that handles end-to-end content research, quality review, and multi-platform publishing. Powered by an autonomous multi-agent architecture, the platform features a custom Retrieval-Augmented Generation (RAG) pipeline for contextual content creation, a centralized FastAPI gateway, and a streamlined Streamlit user interface.

## 🌟 Key Features

* **Multi-Agent Collaboration Engine:** Implemented a specialized crew of AI agents (Research, Reviewer, Supervisor, and Twitter Agents) that coordinate autonomously to brainstorm, refine, and approve high-quality content.
* **Stateful Graph Workflows:** Managed agent interactions, state transitions, and decision loops using structured graphs to ensure reliable execution paths.
* **Context-Aware Generation (RAG):** Built a custom RAG pipeline using document loaders, smart text chunking, and semantic vector embeddings to anchor content generation in factual, user-provided references.
* **Model Context Protocol (MCP) Integration:** Developed dedicated MCP servers (LinkedIn, Twitter, Search) to modularize tools and decouple external data fetching from core business logic.
* **Robust API Gateway & Secure Authentication:** Designed a scalable FastAPI backend featuring secure user authentication, optimized routing tables, and explicit data schemas.
* **Streamlined UI & Containerization:** Built an interactive, intuitive web dashboard using Streamlit to monitor workflows, and containerized the architecture for quick local setup.

---

## 🛠️ Tech Stack & Engineering Focus

* **AI & Agentic Frameworks:** Python, Custom Graph Workflows (LangGraph concepts), RAG (Embedding, Chunking, Retrieval)
* **Backend APIs:** FastAPI, RESTful API design, Pydantic (Schema validation)
* **Database & Cloud Storage:** Supabase (PostgreSQL engine for session persistence, relational tracking, and user auth)
* **Frontend UI:** Streamlit (Dynamic dashboard state management)
* **DevOps & Package Management:** Docker, `uv` / `pyproject.toml` (High-performance dependency handling)

---

## 📊 Cloud Database & RAG Pipeline

* **Supabase Integration:** Leveraged **Supabase** as a fully managed cloud database layer. This architecture offloads state management and data relational mapping to a highly reliable hosted PostgreSQL engine, drastically reducing the memory footprint of our containerized application services.
* **Business Insights:** Transformed raw interaction logs pulled from Supabase into clean data arrays displayed natively within the Streamlit interface to isolate audience growth metrics and visualize overall content ROI.

---

## 📂 Project Architecture

```text
├── research_agent.py      # Gathers factual data and trends
├── reviewer_agent.py      # Quality assurance and tone consistency checks
├── superviser_agent.py    # Directs workflow coordination and approvals
├── twitter_agent.py       # Specializes in platform-specific content optimization
├── api/
│   ├── routes/            # REST API route handlers
│   ├── auth.py            # User authentication and security logic
│   ├── main.py            # FastAPI application entry point
│   └── schemas.py         # Pydantic data validation schemas
├── backend/
│   ├── Dockerfile         # Optimized environment container for backend services
│   └── Dockerfile.frontend# Optimized environment container for the frontend UI
├── dashboard/
│   └── ui.py              # Streamlit-based web dashboard interface
├── database/
│   ├── connection.py      # Database pooling and session lifecycle management
│   ├── models.py          # Relational ORM / database schemas
│   └── queries.py         # Optimized SQL query compilation layer
├── docs/                  # Project documentation and output tracking
├── graph/
│   ├── state.py           # Core graph memory and execution state definitions
│   └── workflow.py        # Compiles agent interactions and decision nodes
├── mcp_servers/           # Model Context Protocol service layers
│   ├── linkedin_server.py # MCP integration for LinkedIn operations
│   ├── search_server.py   # MCP integration for automated web search
│   └── twitter_server.py  # MCP integration for Twitter operations
├── rag/                   # Document ingestion and vector search pipeline
│   ├── chunking.py        # Text splitting algorithms
│   ├── embedding.py       # Generates vector arrays from raw text
│   ├── loader.py          # Document parsing utilities
│   └── retriever.py       # Semantic context matching engine
├── rag_db/                # Local storage vector database instance
├── setup_db.py            # Automated script to initialize relational databases
└── setup_rag.py           # Automated script to bootstrap vector indexes and embeddings

