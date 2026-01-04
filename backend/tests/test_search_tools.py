"""Tests for CourseSearchTool and ToolManager in search_tools.py"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from vector_store import SearchResults


class TestCourseSearchToolExecute:
    """Tests for CourseSearchTool.execute() method"""

    def test_execute_basic_query_returns_formatted_results(self, mock_vector_store, sample_search_results):
        """When query matches content, returns formatted results with course headers"""
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="test query")

        # Should call vector store search
        mock_vector_store.search.assert_called_once_with(
            query="test query",
            course_name=None,
            lesson_number=None
        )
        # Should contain course header
        assert "[MCP Course" in result
        assert "Lesson 1]" in result
        assert "Content about MCP tools" in result

    def test_execute_with_course_filter_passes_to_vector_store(self, mock_vector_store):
        """When course_name provided, passes it to VectorStore.search()"""
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="test query", course_name="MCP")

        mock_vector_store.search.assert_called_once_with(
            query="test query",
            course_name="MCP",
            lesson_number=None
        )

    def test_execute_with_lesson_filter_passes_to_vector_store(self, mock_vector_store):
        """When lesson_number provided, passes it to VectorStore.search()"""
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="test query", lesson_number=2)

        mock_vector_store.search.assert_called_once_with(
            query="test query",
            course_name=None,
            lesson_number=2
        )

    def test_execute_with_both_filters_passes_both(self, mock_vector_store):
        """When both course_name and lesson_number provided, passes both"""
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="test query", course_name="MCP", lesson_number=1)

        mock_vector_store.search.assert_called_once_with(
            query="test query",
            course_name="MCP",
            lesson_number=1
        )

    def test_execute_returns_error_when_search_has_error(self, mock_vector_store, error_search_results):
        """When VectorStore.search() returns SearchResults with error, returns error string"""
        mock_vector_store.search.return_value = error_search_results
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="test query")

        assert result == "Search error: Connection failed"

    def test_execute_returns_empty_message_when_no_results(self, mock_vector_store, empty_search_results):
        """When SearchResults.is_empty() is True, returns 'No relevant content found'"""
        mock_vector_store.search.return_value = empty_search_results
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="test query")

        assert "No relevant content found" in result

    def test_execute_empty_message_includes_course_filter(self, mock_vector_store, empty_search_results):
        """Empty message includes 'in course X' when course_name was provided"""
        mock_vector_store.search.return_value = empty_search_results
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="test query", course_name="MCP")

        assert "in course 'MCP'" in result

    def test_execute_empty_message_includes_lesson_filter(self, mock_vector_store, empty_search_results):
        """Empty message includes 'in lesson N' when lesson_number was provided"""
        mock_vector_store.search.return_value = empty_search_results
        tool = CourseSearchTool(mock_vector_store)

        result = tool.execute(query="test query", lesson_number=3)

        assert "in lesson 3" in result

    def test_execute_stores_sources_for_retrieval(self, mock_vector_store):
        """After execute, last_sources contains formatted source links"""
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="test query")

        # Should have sources stored
        assert len(tool.last_sources) > 0
        # Sources should contain course title
        assert any("MCP Course" in source for source in tool.last_sources)

    def test_format_results_creates_markdown_source_links(self, mock_vector_store):
        """Sources are formatted as [Title - Lesson N](url) markdown"""
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"
        tool = CourseSearchTool(mock_vector_store)

        tool.execute(query="test query")

        # Check that sources contain markdown links
        sources = tool.last_sources
        assert any("](https://example.com" in source for source in sources)


class TestToolManager:
    """Tests for ToolManager class"""

    def test_register_tool_adds_to_tools_dict(self, mock_vector_store):
        """Registering a tool makes it available by name"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)

        manager.register_tool(tool)

        assert "search_course_content" in manager.tools

    def test_register_tool_raises_on_missing_name(self):
        """Raises ValueError if tool definition has no 'name'"""
        manager = ToolManager()
        bad_tool = MagicMock()
        bad_tool.get_tool_definition.return_value = {"description": "no name"}

        with pytest.raises(ValueError, match="Tool must have a 'name'"):
            manager.register_tool(bad_tool)

    def test_get_tool_definitions_returns_all_registered(self, mock_vector_store):
        """Returns list of all tool definitions"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"

    def test_execute_tool_calls_correct_tool(self, mock_vector_store):
        """execute_tool routes to correct tool.execute()"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        result = manager.execute_tool("search_course_content", query="test")

        mock_vector_store.search.assert_called_once()

    def test_execute_tool_returns_not_found_for_unknown(self):
        """Returns "Tool 'X' not found" for unregistered tool"""
        manager = ToolManager()

        result = manager.execute_tool("unknown_tool", query="test")

        assert "Tool 'unknown_tool' not found" in result

    def test_get_last_sources_returns_from_tool_with_sources(self, mock_vector_store):
        """Returns sources from tool that has non-empty last_sources"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute to populate sources
        manager.execute_tool("search_course_content", query="test")

        sources = manager.get_last_sources()
        assert len(sources) > 0

    def test_reset_sources_clears_all_tool_sources(self, mock_vector_store):
        """reset_sources() clears last_sources on all tools"""
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute to populate sources
        manager.execute_tool("search_course_content", query="test")
        assert len(tool.last_sources) > 0

        # Reset and verify cleared
        manager.reset_sources()
        assert len(tool.last_sources) == 0


class TestCourseSearchToolDefinition:
    """Tests for CourseSearchTool.get_tool_definition()"""

    def test_tool_definition_has_required_fields(self, mock_vector_store):
        """Tool definition contains name, description, and input_schema"""
        tool = CourseSearchTool(mock_vector_store)

        definition = tool.get_tool_definition()

        assert "name" in definition
        assert "description" in definition
        assert "input_schema" in definition

    def test_tool_definition_query_is_required(self, mock_vector_store):
        """Tool definition marks query as required parameter"""
        tool = CourseSearchTool(mock_vector_store)

        definition = tool.get_tool_definition()

        assert "query" in definition["input_schema"]["required"]

    def test_tool_definition_course_name_is_optional(self, mock_vector_store):
        """Tool definition has course_name as optional parameter"""
        tool = CourseSearchTool(mock_vector_store)

        definition = tool.get_tool_definition()

        assert "course_name" in definition["input_schema"]["properties"]
        assert "course_name" not in definition["input_schema"]["required"]
