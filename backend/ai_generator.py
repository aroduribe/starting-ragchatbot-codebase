import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Tool Usage:
- Use **search_course_content** for questions about specific course content or detailed educational materials
- Use **get_course_outline** when users ask about course structure, available lessons, or want an overview of a course (returns course title, course link, and all lesson numbers/titles)
- **Up to 2 sequential tool calls per query if needed to gather complete information**
- Synthesize results into accurate, fact-based responses
- If a tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    MAX_TOOL_ROUNDS = 2  # Maximum sequential tool-calling rounds per query

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        Supports up to MAX_TOOL_ROUNDS sequential tool calls.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Initialize messages list for conversation
        messages = [{"role": "user", "content": query}]
        round_count = 0

        while True:
            # Build API parameters for this round
            api_params = {
                **self.base_params,
                "messages": messages,
                "system": system_content
            }

            # Add tools if available and we haven't exceeded max rounds
            if tools and round_count < self.MAX_TOOL_ROUNDS:
                api_params["tools"] = tools
                api_params["tool_choice"] = {"type": "auto"}

            # Get response from Claude with error handling
            try:
                response = self.client.messages.create(**api_params)
            except anthropic.APIError as e:
                return f"I'm having trouble connecting to the AI service. Please try again. (Error: {type(e).__name__})"
            except Exception as e:
                return f"An unexpected error occurred. Please try again. (Error: {type(e).__name__})"

            # Check if tool execution is needed and allowed
            if response.stop_reason == "tool_use" and tool_manager and tools:
                round_count += 1

                # Add assistant's tool use response to messages
                messages.append({"role": "assistant", "content": response.content})

                # Execute all tool calls and collect results
                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_result = tool_manager.execute_tool(
                            content_block.name,
                            **content_block.input
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result
                        })

                # Add tool results as user message
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})

                # Continue loop - next iteration will check if max rounds reached
                continue

            # No tool_use or tools exhausted - validate and return text response
            if not response.content:
                return "I received an empty response. Please try rephrasing your question."

            return response.content[0].text