"""Tests for AIGenerator in ai_generator.py"""

import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os
from dataclasses import dataclass
from typing import List, Any, Dict

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


class TestAIGeneratorGenerateResponse:
    """Tests for AIGenerator.generate_response() method"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_calls_anthropic_api(self, mock_anthropic_class):
        """Calls client.messages.create with correct parameters"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("Test response")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")
        result = generator.generate_response(query="What is MCP?")

        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "test-model"
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_includes_system_prompt(self, mock_anthropic_class):
        """System prompt is included in API call"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("Test response")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")
        generator.generate_response(query="What is MCP?")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "system" in call_kwargs
        assert "search_course_content" in call_kwargs["system"]

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_includes_conversation_history(self, mock_anthropic_class):
        """When history provided, appends to system content"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("Test response")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")
        history = "User: Previous question\nAssistant: Previous answer"
        generator.generate_response(query="What is MCP?", conversation_history=history)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert history in call_kwargs["system"]

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_without_history_uses_base_prompt(self, mock_anthropic_class):
        """When no history, uses only SYSTEM_PROMPT"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("Test response")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")
        generator.generate_response(query="What is MCP?")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == AIGenerator.SYSTEM_PROMPT

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_includes_tools_when_provided(self, mock_anthropic_class):
        """Tools parameter passed to API when provided"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("Test response")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        generator.generate_response(query="What is MCP?", tools=tools)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == tools

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_sets_tool_choice_auto(self, mock_anthropic_class):
        """tool_choice set to {"type": "auto"} when tools provided"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("Test response")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        generator.generate_response(query="What is MCP?", tools=tools)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "auto"}

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_returns_text_for_end_turn(self, mock_anthropic_class):
        """When stop_reason='end_turn', returns content[0].text"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("The answer is 42")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")
        result = generator.generate_response(query="What is the answer?")

        assert result == "The answer is 42"

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_handles_api_error(self, mock_anthropic_class):
        """When API raises exception, returns user-friendly error message"""
        from ai_generator import AIGenerator
        import anthropic

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="API Error",
            request=MagicMock(),
            body=None
        )
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")

        # Error is caught and returns user-friendly message
        result = generator.generate_response(query="What is MCP?")
        assert "trouble connecting" in result
        assert "APIError" in result

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_handles_empty_content(self, mock_anthropic_class):
        """When response.content is empty, returns user-friendly error message"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = MockMessage(content=[], stop_reason="end_turn")
        mock_anthropic_class.return_value = mock_client

        generator = AIGenerator(api_key="test-key", model="test-model")

        # Empty content is handled gracefully
        result = generator.generate_response(query="What is MCP?")
        assert "empty response" in result


class TestAIGeneratorToolExecution:
    """Tests for AIGenerator tool execution in generate_response()"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_executes_tool(self, mock_anthropic_class):
        """Calls tool_manager.execute_tool with correct name and args"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        # First call returns tool_use, second returns text
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            create_text_response("Here is the result")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result content"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="MCP"
        )

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_makes_second_api_call(self, mock_anthropic_class):
        """Makes second API call with tool results"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            create_text_response("Here is the result")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result content"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Should be called twice
        assert mock_client.messages.create.call_count == 2

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_second_call_includes_tools(self, mock_anthropic_class):
        """Second API call includes tools (allows sequential tool calling)"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            create_text_response("Here is the result")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result content"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Second call SHOULD have tools (enables sequential tool calling)
        second_call_kwargs = mock_client.messages.create.call_args_list[1].kwargs
        assert "tools" in second_call_kwargs
        assert second_call_kwargs["tools"] == tools

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_returns_final_text(self, mock_anthropic_class):
        """Returns text from second API response"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            create_text_response("The final answer about MCP")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result content"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        assert result == "The final answer about MCP"

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_passes_tool_error_to_claude(self, mock_anthropic_class):
        """If tool returns error string, passes it as tool_result content"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            create_text_response("I couldn't find results")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        # Simulate tool returning an error
        mock_tool_manager.execute_tool.return_value = "No course found matching 'invalid'"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Check that error string was passed in the second call
        second_call_kwargs = mock_client.messages.create.call_args_list[1].kwargs
        messages = second_call_kwargs["messages"]
        # Find the tool_result message
        tool_result_msg = next(m for m in messages if m["role"] == "user" and isinstance(m["content"], list))
        tool_result_content = tool_result_msg["content"][0]["content"]
        assert "No course found matching 'invalid'" in tool_result_content

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_handles_multiple_tools(self, mock_anthropic_class):
        """Processes all tool_use blocks in response"""
        from ai_generator import AIGenerator

        # Response with multiple tool uses
        multi_tool_response = MockMessage(
            content=[
                MockToolUseBlock(name="search_course_content", input={"query": "MCP"}, id="tool1"),
                MockToolUseBlock(name="get_course_outline", input={"course_name": "MCP"}, id="tool2")
            ],
            stop_reason="tool_use"
        )

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            multi_tool_response,
            create_text_response("Combined results")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content"}, {"name": "get_course_outline"}]
        generator.generate_response(
            query="Tell me about MCP",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Should execute both tools
        assert mock_tool_manager.execute_tool.call_count == 2

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_handles_second_api_error(self, mock_anthropic_class):
        """If second API call fails, returns user-friendly error message"""
        from ai_generator import AIGenerator
        import anthropic

        mock_client = MagicMock()
        # First call returns tool_use, second call raises error
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            anthropic.APIError(message="Rate limited", request=MagicMock(), body=None)
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result content"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Error is caught and returns user-friendly message
        assert "trouble connecting" in result
        assert "APIError" in result

    @patch('ai_generator.anthropic.Anthropic')
    def test_handle_tool_execution_handles_empty_final_response(self, mock_anthropic_class):
        """If final response is empty, returns user-friendly error message"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            MockMessage(content=[], stop_reason="end_turn")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result content"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Empty content is handled gracefully
        assert "empty response" in result


class TestAIGeneratorConfiguration:
    """Tests for AIGenerator initialization and configuration"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_init_sets_model(self, mock_anthropic_class):
        """Constructor sets model correctly"""
        from ai_generator import AIGenerator

        generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

        assert generator.model == "claude-sonnet-4-20250514"

    @patch('ai_generator.anthropic.Anthropic')
    def test_init_creates_anthropic_client(self, mock_anthropic_class):
        """Constructor creates Anthropic client with API key"""
        from ai_generator import AIGenerator

        generator = AIGenerator(api_key="test-api-key", model="test-model")

        mock_anthropic_class.assert_called_once_with(api_key="test-api-key")

    @patch('ai_generator.anthropic.Anthropic')
    def test_base_params_include_temperature_zero(self, mock_anthropic_class):
        """Base parameters include temperature=0 for deterministic output"""
        from ai_generator import AIGenerator

        generator = AIGenerator(api_key="test-key", model="test-model")

        assert generator.base_params["temperature"] == 0

    @patch('ai_generator.anthropic.Anthropic')
    def test_base_params_include_max_tokens(self, mock_anthropic_class):
        """Base parameters include max_tokens"""
        from ai_generator import AIGenerator

        generator = AIGenerator(api_key="test-key", model="test-model")

        assert generator.base_params["max_tokens"] == 800

    @patch('ai_generator.anthropic.Anthropic')
    def test_max_tool_rounds_constant_exists(self, mock_anthropic_class):
        """MAX_TOOL_ROUNDS constant is defined"""
        from ai_generator import AIGenerator

        assert hasattr(AIGenerator, 'MAX_TOOL_ROUNDS')
        assert AIGenerator.MAX_TOOL_ROUNDS == 2


class TestSequentialToolCalling:
    """Tests for sequential tool calling (up to MAX_TOOL_ROUNDS)"""

    @patch('ai_generator.anthropic.Anthropic')
    def test_two_sequential_tool_calls(self, mock_anthropic_class):
        """Claude can make two sequential tool calls"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        # Round 1: tool_use, Round 2: tool_use, Final: text
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "lesson 4"}, "tool1"),
            create_tool_use_response("search_course_content", {"query": "topic from lesson 4"}, "tool2"),
            create_text_response("Here is the comparison")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="Compare lesson 4 with similar topics",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Should make 3 API calls total
        assert mock_client.messages.create.call_count == 3
        # Should execute tool twice
        assert mock_tool_manager.execute_tool.call_count == 2
        # Should return final text
        assert result == "Here is the comparison"

    @patch('ai_generator.anthropic.Anthropic')
    def test_max_rounds_forces_final_response_without_tools(self, mock_anthropic_class):
        """After MAX_TOOL_ROUNDS, third call excludes tools"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "first"}, "tool1"),
            create_tool_use_response("search_course_content", {"query": "second"}, "tool2"),
            create_text_response("Final answer after max rounds")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        generator.generate_response(
            query="Complex query",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Third call should NOT have tools (forces text response)
        third_call_kwargs = mock_client.messages.create.call_args_list[2].kwargs
        assert "tools" not in third_call_kwargs

    @patch('ai_generator.anthropic.Anthropic')
    def test_single_tool_call_still_works(self, mock_anthropic_class):
        """Single tool call (existing behavior) still works"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "MCP"}),
            create_text_response("The result about MCP")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        assert mock_client.messages.create.call_count == 2
        assert mock_tool_manager.execute_tool.call_count == 1
        assert result == "The result about MCP"

    @patch('ai_generator.anthropic.Anthropic')
    def test_no_tool_use_exits_immediately(self, mock_anthropic_class):
        """Direct text response exits loop without tool calls"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.return_value = create_text_response("Direct answer")
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="What is 2+2?",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Only one API call, no tool execution
        assert mock_client.messages.create.call_count == 1
        mock_tool_manager.execute_tool.assert_not_called()
        assert result == "Direct answer"

    @patch('ai_generator.anthropic.Anthropic')
    def test_messages_accumulate_across_rounds(self, mock_anthropic_class):
        """Messages from each round are accumulated correctly"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "first"}, "tool1"),
            create_tool_use_response("search_course_content", {"query": "second"}, "tool2"),
            create_text_response("Final answer")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        generator.generate_response(
            query="Complex query",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Check third call has accumulated messages
        third_call_kwargs = mock_client.messages.create.call_args_list[2].kwargs
        messages = third_call_kwargs["messages"]

        # Should have: user query, assistant tool1, user result1, assistant tool2, user result2
        assert len(messages) == 5
        assert messages[0]["role"] == "user"  # Original query
        assert messages[1]["role"] == "assistant"  # First tool use
        assert messages[2]["role"] == "user"  # First tool result
        assert messages[3]["role"] == "assistant"  # Second tool use
        assert messages[4]["role"] == "user"  # Second tool result

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_failure_continues_to_next_round(self, mock_anthropic_class):
        """Tool returning error string continues loop (Claude handles error)"""
        from ai_generator import AIGenerator

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            create_tool_use_response("search_course_content", {"query": "invalid"}),
            create_text_response("I couldn't find that information")
        ]
        mock_anthropic_class.return_value = mock_client

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Error: No course found matching 'invalid'"

        generator = AIGenerator(api_key="test-key", model="test-model")
        tools = [{"name": "search_course_content", "description": "Search"}]
        result = generator.generate_response(
            query="Tell me about invalid course",
            tools=tools,
            tool_manager=mock_tool_manager
        )

        # Loop continues, error passed to Claude
        assert mock_client.messages.create.call_count == 2
        assert result == "I couldn't find that information"
