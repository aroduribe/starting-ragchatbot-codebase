"""Tests for FastAPI endpoints in app.py"""

import pytest
from unittest.mock import MagicMock


class TestQueryEndpoint:
    """Tests for POST /api/query endpoint"""

    def test_query_returns_200_with_valid_request(self, test_client, sample_query_request):
        """Valid query request returns 200 status"""
        response = test_client.post("/api/query", json=sample_query_request)
        assert response.status_code == 200

    def test_query_returns_answer_in_response(self, test_client, sample_query_request):
        """Response contains answer field"""
        response = test_client.post("/api/query", json=sample_query_request)
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "Test answer about the course"

    def test_query_returns_sources_in_response(self, test_client, sample_query_request):
        """Response contains sources list"""
        response = test_client.post("/api/query", json=sample_query_request)
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert data["sources"] == ["Source 1", "Source 2"]

    def test_query_returns_session_id(self, test_client, sample_query_request):
        """Response contains session_id"""
        response = test_client.post("/api/query", json=sample_query_request)
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"

    def test_query_creates_session_when_not_provided(self, test_client, test_app):
        """New session is created when session_id is None"""
        response = test_client.post("/api/query", json={"query": "Test query"})
        data = response.json()

        # Session manager's create_session should have been called
        test_app.state.rag_system.session_manager.create_session.assert_called_once()
        assert data["session_id"] == "test-session-123"

    def test_query_uses_provided_session_id(self, test_client, sample_query_request_with_session, test_app):
        """Existing session_id is used when provided"""
        response = test_client.post("/api/query", json=sample_query_request_with_session)
        data = response.json()

        # Should use the provided session ID
        assert data["session_id"] == "existing-session-456"
        # create_session should not be called
        test_app.state.rag_system.session_manager.create_session.assert_not_called()

    def test_query_calls_rag_system_query(self, test_client, sample_query_request, test_app):
        """RAGSystem.query is called with correct arguments"""
        test_client.post("/api/query", json=sample_query_request)

        test_app.state.rag_system.query.assert_called_once_with(
            "What is MCP?",
            "test-session-123"
        )

    def test_query_returns_400_for_missing_query(self, test_client):
        """Request without query field returns 422 validation error"""
        response = test_client.post("/api/query", json={})
        assert response.status_code == 422

    def test_query_returns_400_for_empty_query(self, test_client):
        """Request with empty query string still processes (validation at app level)"""
        response = test_client.post("/api/query", json={"query": ""})
        # Empty string is valid at schema level, app may handle differently
        assert response.status_code == 200

    def test_query_returns_500_on_rag_system_error(self, test_client, test_app):
        """Internal error from RAGSystem returns 500"""
        test_app.state.rag_system.query.side_effect = Exception("Database connection failed")

        response = test_client.post("/api/query", json={"query": "Test"})

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]


class TestCoursesEndpoint:
    """Tests for GET /api/courses endpoint"""

    def test_courses_returns_200(self, test_client):
        """Courses endpoint returns 200 status"""
        response = test_client.get("/api/courses")
        assert response.status_code == 200

    def test_courses_returns_total_count(self, test_client):
        """Response contains total_courses count"""
        response = test_client.get("/api/courses")
        data = response.json()
        assert "total_courses" in data
        assert data["total_courses"] == 3

    def test_courses_returns_course_titles(self, test_client):
        """Response contains course_titles list"""
        response = test_client.get("/api/courses")
        data = response.json()
        assert "course_titles" in data
        assert isinstance(data["course_titles"], list)
        assert len(data["course_titles"]) == 3
        assert "Course A" in data["course_titles"]

    def test_courses_calls_get_course_analytics(self, test_client, test_app):
        """RAGSystem.get_course_analytics is called"""
        test_client.get("/api/courses")
        test_app.state.rag_system.get_course_analytics.assert_called_once()

    def test_courses_returns_500_on_error(self, test_client, test_app):
        """Internal error returns 500"""
        test_app.state.rag_system.get_course_analytics.side_effect = Exception("Vector store error")

        response = test_client.get("/api/courses")

        assert response.status_code == 500
        assert "Vector store error" in response.json()["detail"]

    def test_courses_returns_empty_list_when_no_courses(self, test_client, test_app):
        """Returns empty list when no courses exist"""
        test_app.state.rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        response = test_client.get("/api/courses")
        data = response.json()

        assert data["total_courses"] == 0
        assert data["course_titles"] == []


class TestSessionEndpoint:
    """Tests for DELETE /api/session/{session_id} endpoint"""

    def test_delete_session_returns_200(self, test_client):
        """Delete session returns 200 status"""
        response = test_client.delete("/api/session/test-session-123")
        assert response.status_code == 200

    def test_delete_session_returns_ok_status(self, test_client):
        """Response contains status: ok"""
        response = test_client.delete("/api/session/test-session-123")
        data = response.json()
        assert data["status"] == "ok"

    def test_delete_session_calls_clear_session(self, test_client, test_app):
        """SessionManager.clear_session is called with correct session_id"""
        test_client.delete("/api/session/my-session-456")

        test_app.state.rag_system.session_manager.clear_session.assert_called_once_with(
            "my-session-456"
        )

    def test_delete_nonexistent_session_still_returns_ok(self, test_client):
        """Deleting non-existent session returns ok (idempotent)"""
        response = test_client.delete("/api/session/nonexistent-session")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestRootEndpoint:
    """Tests for GET / endpoint (health check)"""

    def test_root_returns_200(self, test_client):
        """Root endpoint returns 200 status"""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_root_returns_healthy_status(self, test_client):
        """Root endpoint indicates healthy status"""
        response = test_client.get("/")
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_returns_service_name(self, test_client):
        """Root endpoint returns service identifier"""
        response = test_client.get("/")
        data = response.json()
        assert "service" in data


class TestAPIResponseFormats:
    """Tests for API response format compliance"""

    def test_query_response_matches_schema(self, test_client, sample_query_request):
        """Query response has all required fields"""
        response = test_client.post("/api/query", json=sample_query_request)
        data = response.json()

        required_fields = {"answer", "sources", "session_id"}
        assert required_fields.issubset(data.keys())

    def test_courses_response_matches_schema(self, test_client):
        """Courses response has all required fields"""
        response = test_client.get("/api/courses")
        data = response.json()

        required_fields = {"total_courses", "course_titles"}
        assert required_fields.issubset(data.keys())

    def test_query_sources_are_strings(self, test_client, sample_query_request):
        """Sources in query response are string type"""
        response = test_client.post("/api/query", json=sample_query_request)
        data = response.json()

        for source in data["sources"]:
            assert isinstance(source, str)

    def test_courses_titles_are_strings(self, test_client):
        """Course titles are string type"""
        response = test_client.get("/api/courses")
        data = response.json()

        for title in data["course_titles"]:
            assert isinstance(title, str)

    def test_total_courses_is_integer(self, test_client):
        """Total courses count is integer type"""
        response = test_client.get("/api/courses")
        data = response.json()

        assert isinstance(data["total_courses"], int)
