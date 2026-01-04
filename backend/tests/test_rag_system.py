"""Tests for RAGSystem in rag_system.py"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRAGSystemQuery:
    """Tests for RAGSystem.query() method"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_creates_session_if_not_provided(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """When session_id is None, still processes query"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "Response"
        mock_ai_cls.return_value = mock_ai_instance

        mock_session_instance = MagicMock()
        mock_session_instance.get_conversation_history.return_value = None
        mock_session_cls.return_value = mock_session_instance

        rag = RAGSystem(mock_config)
        response, sources = rag.query("What is MCP?", session_id=None)

        # Should still work without session
        assert response == "Response"
        # History should not be fetched when no session
        mock_session_instance.get_conversation_history.assert_not_called()

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_uses_existing_session_history(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """When session_id provided, retrieves history from SessionManager"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "Response"
        mock_ai_cls.return_value = mock_ai_instance

        mock_session_instance = MagicMock()
        mock_session_instance.get_conversation_history.return_value = "Previous conversation"
        mock_session_cls.return_value = mock_session_instance

        rag = RAGSystem(mock_config)
        rag.query("What is MCP?", session_id="session123")

        mock_session_instance.get_conversation_history.assert_called_once_with("session123")

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_passes_tools_to_ai_generator(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """tool_definitions from ToolManager passed to generate_response"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "Response"
        mock_ai_cls.return_value = mock_ai_instance

        rag = RAGSystem(mock_config)
        rag.query("What is MCP?")

        call_kwargs = mock_ai_instance.generate_response.call_args.kwargs
        assert "tools" in call_kwargs
        # Should have tool definitions (search_course_content and get_course_outline)
        assert len(call_kwargs["tools"]) >= 1

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_passes_tool_manager_to_ai_generator(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """tool_manager passed for tool execution"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "Response"
        mock_ai_cls.return_value = mock_ai_instance

        rag = RAGSystem(mock_config)
        rag.query("What is MCP?")

        call_kwargs = mock_ai_instance.generate_response.call_args.kwargs
        assert "tool_manager" in call_kwargs
        assert call_kwargs["tool_manager"] is not None

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_retrieves_sources_from_tool_manager(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """After response, calls get_last_sources()"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "Response"
        mock_ai_cls.return_value = mock_ai_instance

        rag = RAGSystem(mock_config)
        # Mock the tool_manager's get_last_sources
        rag.tool_manager.get_last_sources = MagicMock(return_value=["Source 1", "Source 2"])

        response, sources = rag.query("What is MCP?")

        rag.tool_manager.get_last_sources.assert_called_once()
        assert sources == ["Source 1", "Source 2"]

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_resets_sources_after_retrieval(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Calls reset_sources() after getting sources"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "Response"
        mock_ai_cls.return_value = mock_ai_instance

        rag = RAGSystem(mock_config)
        rag.tool_manager.reset_sources = MagicMock()

        rag.query("What is MCP?")

        rag.tool_manager.reset_sources.assert_called_once()

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_updates_session_history(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Calls session_manager.add_exchange with query and response"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "The answer"
        mock_ai_cls.return_value = mock_ai_instance

        mock_session_instance = MagicMock()
        mock_session_cls.return_value = mock_session_instance

        rag = RAGSystem(mock_config)
        rag.query("What is MCP?", session_id="session123")

        mock_session_instance.add_exchange.assert_called_once_with(
            "session123", "What is MCP?", "The answer"
        )

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_returns_response_and_sources_tuple(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Returns (response_text, sources_list) tuple"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "The answer"
        mock_ai_cls.return_value = mock_ai_instance

        rag = RAGSystem(mock_config)
        rag.tool_manager.get_last_sources = MagicMock(return_value=["Source A"])

        result = rag.query("What is MCP?")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "The answer"
        assert result[1] == ["Source A"]

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_propagates_ai_generator_error(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Exceptions from AIGenerator propagate to caller"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.side_effect = Exception("API Error")
        mock_ai_cls.return_value = mock_ai_instance

        rag = RAGSystem(mock_config)

        # Error should propagate (not caught)
        with pytest.raises(Exception, match="API Error"):
            rag.query("What is MCP?")

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_query_formats_prompt_correctly(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Query is formatted as expected before passing to AI"""
        from rag_system import RAGSystem

        mock_ai_instance = MagicMock()
        mock_ai_instance.generate_response.return_value = "Response"
        mock_ai_cls.return_value = mock_ai_instance

        rag = RAGSystem(mock_config)
        rag.query("What is MCP?")

        call_kwargs = mock_ai_instance.generate_response.call_args.kwargs
        # Should contain the query in the formatted prompt
        assert "What is MCP?" in call_kwargs["query"]


class TestRAGSystemInitialization:
    """Tests for RAGSystem initialization"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_init_creates_all_components(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Constructor initializes all required components"""
        from rag_system import RAGSystem

        rag = RAGSystem(mock_config)

        mock_doc_cls.assert_called_once()
        mock_vector_cls.assert_called_once()
        mock_ai_cls.assert_called_once()
        mock_session_cls.assert_called_once()

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_init_registers_search_tools(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Constructor registers search tools with ToolManager"""
        from rag_system import RAGSystem

        rag = RAGSystem(mock_config)

        # Should have both tools registered
        tool_names = list(rag.tool_manager.tools.keys())
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names


class TestRAGSystemAddCourseDocument:
    """Tests for RAGSystem.add_course_document()"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_add_course_document_processes_document(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Calls DocumentProcessor.process_course_document"""
        from rag_system import RAGSystem
        from models import Course, Lesson

        mock_doc_instance = MagicMock()
        mock_course = Course(title="Test Course", instructor="Test", course_link="", lessons=[])
        mock_doc_instance.process_course_document.return_value = (mock_course, [])
        mock_doc_cls.return_value = mock_doc_instance

        rag = RAGSystem(mock_config)
        rag.add_course_document("/path/to/course.txt")

        mock_doc_instance.process_course_document.assert_called_once_with("/path/to/course.txt")

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_add_course_document_handles_processing_error(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Returns (None, 0) on exception"""
        from rag_system import RAGSystem

        mock_doc_instance = MagicMock()
        mock_doc_instance.process_course_document.side_effect = Exception("Parse error")
        mock_doc_cls.return_value = mock_doc_instance

        rag = RAGSystem(mock_config)
        course, count = rag.add_course_document("/path/to/bad_course.txt")

        assert course is None
        assert count == 0


class TestRAGSystemGetCourseAnalytics:
    """Tests for RAGSystem.get_course_analytics()"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    def test_get_course_analytics_returns_stats(
        self, mock_session_cls, mock_ai_cls, mock_vector_cls, mock_doc_cls, mock_config
    ):
        """Returns dict with total_courses and course_titles"""
        from rag_system import RAGSystem

        mock_vector_instance = MagicMock()
        mock_vector_instance.get_course_count.return_value = 3
        mock_vector_instance.get_existing_course_titles.return_value = ["Course A", "Course B", "Course C"]
        mock_vector_cls.return_value = mock_vector_instance

        rag = RAGSystem(mock_config)
        analytics = rag.get_course_analytics()

        assert analytics["total_courses"] == 3
        assert len(analytics["course_titles"]) == 3
