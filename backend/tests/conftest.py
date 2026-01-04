"""Shared test fixtures and mocks for RAG chatbot tests."""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Any, Dict
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
