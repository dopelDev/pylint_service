import pytest
import socket
import threading
from app.pylint_service.pylint_service import start_server, run_pylint, check_vars_environment, handle_client
from app.pylint_service.pylint_service import EnvironmentVariableError, StatusEnvironmentVariable

# Mock environment variables for testing
@pytest.fixture(scope="module", autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("IP_ADDRESS", "127.0.0.1")
    monkeypatch.setenv("PORT", "8888")


# Test the environment variable check function
def test_check_vars_environment():
    # Test with valid environment variables
    env_vars = check_vars_environment()
    assert env_vars.status is True
    assert env_vars.IP_ADDRESS == "127.0.0.1"
    assert env_vars.PORT == 8888

    # Test with missing IP_ADDRESS
    with pytest.raises(EnvironmentVariableError):
        with pytest.monkeypatch.context() as m:
            m.delenv("IP_ADDRESS", raising=False)
            check_vars_environment()

# Test the pylint runner
def test_run_pylint_valid_code():
    code = "def foo():\n    return 42\n"
    output = run_pylint(code)
    assert "Your code has been rated" in output

def test_run_pylint_invalid_code():
    code = "def foo(\n"
    output = run_pylint(code)
    assert "E0001" in output  # Pylint should report a syntax error


# Test the client-server interaction
def test_client_server_interaction(monkeypatch):
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Create a client socket to connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 8888))

    try:
        # Send Python code to the server
        code = "def foo():\n    return 42\n<<EOF>>"
        client_socket.sendall(code.encode('utf-8'))

        # Receive the server's response
        response = client_socket.recv(4096).decode('utf-8')
        assert "Your code has been rated" in response

    finally:
        client_socket.close()
        server_thread.join(timeout=1)

