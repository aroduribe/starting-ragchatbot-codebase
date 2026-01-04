"""Shared test fixtures and mocks for RAG chatbot tests."""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Any, Dict, Optional
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel


# Mock response classes to simulate Anthropic API responses
@dataclass
class MockTextBlock:
    """Mock Anthropic TextBlock response"""
    type: str = "text"
    text: str = "Mock response"


@dataclass
class MockToolUseBlock:
    """Mock Anthropic ToolUseBlock response"""
    type: str = "tool_use"
    id: str = "toolu_123"
    name: str = "search_course_content"
    input: Dict[str, Any] = None

    def __post_init__(self):
        if self.input is None:
            self.input = {"query": "test query"}


@dataclass
class MockMessage:
    """Mock Anthropic Message response"""
    content: List[Any]
    stop_reason: str = "end_turn"


def create_text_response(text: str) -> MockMessage:
    """Create a mock text response from Claude"""
    return MockMessage(
        content=[MockTextBlock(text=text)],
        stop_reason="end_turn"
    )


def create_tool_use_response(tool_name: str, tool_input: dict, tool_id: str = "toolu_123") -> MockMessage:
    """Create a mock tool use response from Claude"""
    return MockMessage(
        content=[MockToolUseBlock(name=tool_name, input=tool_input, id=tool_id)],
        stop_reason="tool_use"
    )


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client"""
    mock_client = MagicMock()
    mock_client.messages.create = MagicMock(return_value=create_text_response("Mock response"))
    return mock_client


@pytest.fixture
def sample_search_results():
    """Sample SearchResults for testing"""
    from vector_store import SearchResults
    return SearchResults(
        documents=["Content about MCP tools", "More MCP content"],
        metadata=[
            {"course_title": "MCP Course", "lesson_number": 1},
            {"course_title": "MCP Course", "lesson_number": 2}
        ],
        distances=[0.1, 0.2]
    )


@pytest.fixture
def empty_search_results():
    """Empty SearchResults for testing"""
    from vector_store import SearchResults
    return SearchResults(documents=[], metadata=[], distances=[])


@pytest.fixture
def error_search_results():
    """SearchResults with error for testing"""
    from vector_store import SearchResults
    return SearchResults.empty("Search error: Connection failed")


@pytest.fixture
def mock_vector_store(sample_search_results):
    """Create a mock VectorStore"""
    mock_store = MagicMock()
    mock_store.search = MagicMock(return_value=sample_search_results)
    mock_store._resolve_course_name = MagicMock(return_value="MCP Course")
    mock_store.get_lesson_link = MagicMock(return_value="https://example.com/lesson1")
    mock_store.get_course_link = MagicMock(return_value="https://example.com/course")
    mock_store.get_all_courses_metadata = MagicMock(return_value=[])
    return mock_store


@pytest.fixture
def mock_config():
    """Create a mock config object"""
    config = MagicMock()
    config.ANTHROPIC_API_KEY = "test-api-key"
    config.ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.CHROMA_PATH = "./test_chroma_db"
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    return config


# ============================================================================
# API Testing Fixtures
# ============================================================================

# Pydantic models for API tests (mirrors app.py models)
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[str]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


@pytest.fixture
def mock_rag_system():
    """Create a mock RAGSystem for API tests"""
    mock_rag = MagicMock()
    mock_rag.query.return_value = ("Test answer about the course", ["Source 1", "Source 2"])
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 3,
        "course_titles": ["Course A", "Course B", "Course C"]
    }
    mock_rag.session_manager = MagicMock()
    mock_rag.session_manager.create_session.return_value = "test-session-123"
    mock_rag.session_manager.clear_session = MagicMock()
    return mock_rag


def create_test_app(mock_rag_system):
    """
    Create a FastAPI test app with endpoints defined inline.
    This avoids importing app.py which mounts static files that don't exist in tests.
    """
    app = FastAPI(title="Test RAG API")

    # Store the mock RAG system in app state
    app.state.rag_system = mock_rag_system

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            rag = app.state.rag_system
            session_id = request.session_id
            if not session_id:
                session_id = rag.session_manager.create_session()

            answer, sources = rag.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            rag = app.state.rag_system
            analytics = rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/session/{session_id}")
    async def delete_session(session_id: str):
        """Delete a session and clear its history"""
        rag = app.state.rag_system
        rag.session_manager.clear_session(session_id)
        return {"status": "ok"}

    @app.get("/")
    async def root():
        """Health check endpoint"""
        return {"status": "healthy", "service": "RAG API"}

    return app


@pytest.fixture
def test_app(mock_rag_system):
    """Create a test FastAPI app with mocked dependencies"""
    return create_test_app(mock_rag_system)


@pytest.fixture
def test_client(test_app):
    """Create a TestClient for the test app"""
    return TestClient(test_app)


@pytest.fixture
def sample_query_request():
    """Sample query request data"""
    return {"query": "What is MCP?", "session_id": None}


@pytest.fixture
def sample_query_request_with_session():
    """Sample query request with existing session"""
    return {"query": "Tell me more about that", "session_id": "existing-session-456"}
