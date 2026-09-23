"""Offline checks of input validation and the model-service boundary."""

from unittest.mock import MagicMock

import httpx
import pytest
from ollama import ChatResponse, ResponseError

import llm_client


@pytest.fixture
def client_factory(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr(llm_client, "Client", factory)
    return factory


def test_returns_generated_text_and_requests_non_thinking_local_chat(client_factory):
    client = client_factory.return_value.__enter__.return_value
    client.chat.return_value = ChatResponse(
        message={
            "role": "assistant",
            "content": " Hello! ",
            "thinking": "Not the reply",
        }
    )
    assert llm_client.ask_llm(" Hi ") == "Hello!"
    kwargs = client.chat.call_args.kwargs
    assert kwargs["messages"] == [{"role": "user", "content": "Hi"}]
    assert kwargs["model"] == "qwen3:1.7b"
    assert kwargs["think"] is False
    assert kwargs["stream"] is False
    assert client_factory.call_args.kwargs["host"] == "http://127.0.0.1:11434"
    client_factory.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("prompt", ["", " \n\t", None, 42])
def test_invalid_input_never_contacts_server(client_factory, prompt):
    with pytest.raises(ValueError, match="non-empty"):
        llm_client.ask_llm(prompt)
    client_factory.assert_not_called()


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (ConnectionError("offline"), "scripts/ollama.sh serve"),
        (httpx.ReadTimeout("slow"), "timed out"),
        (ResponseError("missing", status_code=404), "pull qwen3:1.7b"),
        (ResponseError("internal", status_code=500), "HTTP 500"),
        (httpx.RemoteProtocolError("disconnected"), "connection to Ollama failed"),
    ],
)
def test_service_failures_are_not_returned_as_replies(client_factory, failure, message):
    client_factory.return_value.__enter__.return_value.chat.side_effect = failure
    with pytest.raises(llm_client.LLMError, match=message):
        llm_client.ask_llm("Hello")


@pytest.mark.parametrize("content", [None, "", "   "])
def test_empty_model_output_is_rejected(client_factory, content):
    client_factory.return_value.__enter__.return_value.chat.return_value = ChatResponse(
        message={"role": "assistant", "content": content}
    )
    with pytest.raises(llm_client.LLMError, match="no reply"):
        llm_client.ask_llm("Hello")


def test_cli_handles_invalid_input_without_traceback(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm_client.py", ""])
    assert llm_client.main() == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Input error: Enter a non-empty text prompt.\n"
