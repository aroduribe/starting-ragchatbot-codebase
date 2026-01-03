# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Always use `uv` for running Python and managing dependencies** (not pip or python directly).

```bash
# Start the development server
./run.sh
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000

# Install dependencies
uv sync

# Run a Python file
uv run python <file.py>

# Add a dependency
uv add <package>
```

The app runs at http://localhost:8000 (web UI) and http://localhost:8000/docs (API docs).

## Architecture

This is a RAG (Retrieval-Augmented Generation) chatbot that answers questions about educational course materials.

### Query Flow

```
Frontend (script.js)
    → POST /api/query
    → FastAPI (app.py)
    → RAGSystem.query()
    → AIGenerator calls Claude with tools
    → If tool_use: ToolManager executes search
    → VectorStore queries ChromaDB
    → Results flow back through the chain
    → Frontend renders response with sources
```

### Backend Components (`backend/`)

| File | Purpose |
|------|---------|
| `app.py` | FastAPI endpoints, serves frontend, loads docs on startup |
| `rag_system.py` | Orchestrator: ties together all components |
| `ai_generator.py` | Claude API client with tool execution loop |
| `search_tools.py` | Tool definitions (`CourseSearchTool`) and `ToolManager` |
| `vector_store.py` | ChromaDB wrapper with fuzzy course name resolution |
| `document_processor.py` | Parses course docs, chunks text with overlap |
| `session_manager.py` | In-memory conversation history per session |
| `config.py` | Settings: chunk size (800), overlap (100), model, paths |

### Frontend (`frontend/`)

Vanilla HTML/CSS/JS with `marked.js` for markdown rendering. Communicates via REST API.

### Document Format (`docs/`)

Course documents follow this structure:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson_title]
Lesson Link: [url]
[content...]

Lesson 1: [lesson_title]
...
```

### Key Design Patterns

- **Tool-based RAG**: Claude decides when to search using the `search_course_content` tool
- **Two-step Claude calls**: Initial call → tool execution → final response with results
- **Fuzzy course matching**: VectorStore resolves partial names (e.g., "MCP") to full titles via embeddings
- **Session context**: Conversation history maintained across queries (last 2 exchanges)
