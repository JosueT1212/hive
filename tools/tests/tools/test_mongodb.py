"""
Unit tests for the MongoDB Tool.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP

# Adjust this import if your file path is slightly different
from aden_tools.tools.mongodb_tool import register_tools


@pytest.fixture
def mcp():
    return FastMCP("test-server")


@pytest.fixture
def tools(mcp):
    """Register the tools and return a dictionary of callable functions."""
    registered_tools = {}
    mock_mcp = MagicMock()

    def mock_tool(**kwargs):
        def decorator(f):
            # Save the function in the dictionary using its name
            registered_tools[f.__name__] = f
            return f

        return decorator

    mock_mcp.tool = mock_tool

    # Register the tools in our mock
    register_tools(mock_mcp)
    return registered_tools


# This fixture automatically injects the fake environment variable into all tests
@pytest.fixture(autouse=True)
def mock_env():
    with patch.dict("os.environ", {"MONGODB_URI": "mongodb+srv://fake:fake@cluster"}):
        yield


def test_mongodb_ping_database_success(tools):
    tool_func = tools["mongodb_ping_database"]

    patch_target = "aden_tools.tools.mongodb_tool.MongoClient"
    with patch(patch_target) as mock_mongo_class:
        # Simulate that the 'ping' command works correctly
        mock_client_instance = MagicMock()
        mock_client_instance.admin.command.return_value = {"ok": 1}
        mock_mongo_class.return_value = mock_client_instance

        result = tool_func()

        assert result["success"] is True
        assert "Successfully connected" in result["message"]
        mock_client_instance.admin.command.assert_called_once_with('ping')


def test_mongodb_insert_document_success(tools):
    tool_func = tools["mongodb_insert_document"]

    patch_target = "aden_tools.tools.mongodb_tool.MongoClient"
    with patch(patch_target) as mock_mongo_class:
        # Prepare the collection mock to return an inserted ID
        mock_collection = MagicMock()
        mock_collection.insert_one.return_value.inserted_id = "507f1f77bcf86cd799439011"

        # Simulate the access: client[database][collection]
        mock_mongo_class.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection

        doc_json = '{"name": "Josue", "role": "admin"}'
        result = tool_func(database="test_db", collection="test_col", document_json=doc_json)

        assert result["success"] is True
        assert result["inserted_id"] == "507f1f77bcf86cd799439011"
        mock_collection.insert_one.assert_called_once_with({"name": "Josue", "role": "admin"})


def test_mongodb_insert_invalid_json(tools):
    tool_func = tools["mongodb_insert_document"]

    # We don't need to mock MongoDB here because it should fail before connecting
    result = tool_func(database="test_db", collection="test_col", document_json="this is not json")

    assert "error" in result
    assert "Invalid JSON format" in result["error"]


def test_mongodb_find_document_success(tools):
    tool_func = tools["mongodb_find_document"]

    patch_target = "aden_tools.tools.mongodb_tool.MongoClient"
    with patch(patch_target) as mock_mongo_class:
        mock_collection = MagicMock()

        # Simulate the MongoDB cursor returning a list with one document
        mock_cursor = [{"_id": "507f191e810c19729de860ea", "name": "Josue"}]
        mock_collection.find.return_value.limit.return_value = mock_cursor

        mock_mongo_class.return_value.__getitem__.return_value.__getitem__.return_value = mock_collection

        query_json = '{"name": "Josue"}'
        result = tool_func(database="test_db", collection="test_col", query_json=query_json, limit=5)

        assert result["success"] is True
        assert result["count"] == 1
        assert result["data"][0]["name"] == "Josue"
        
        # Verify that the database was called with the correct dictionary
        mock_collection.find.assert_called_once_with({"name": "Josue"})


def test_mongodb_missing_credentials(tools):
    tool_func = tools["mongodb_ping_database"]

    # Temporarily clear the fake environment to verify the tool fails gracefully
    with patch.dict("os.environ", {}, clear=True):
        result = tool_func()

        assert "error" in result
        assert "MongoDB URI not configured" in result["error"]
        assert "help" in result
