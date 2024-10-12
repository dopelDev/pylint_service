import pytest
import socket
import threading
from app.module.pylint_service import start_server, run_pylint, check_vars_environment, handle_client
from app.module.pylint_service import EnvironmentVariableError, StatusEnvironmentVariable

# Fixture para mockear las variables de entorno
@pytest.fixture(scope="module", autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("IP_ADDRESS", "127.0.0.1")
    monkeypatch.setenv("PORT", "8888")


# Test de la función de verificación de variables de entorno
def test_check_vars_environment(monkeypatch):
    # Test con variables de entorno válidas
    env_vars = check_vars_environment()
    assert env_vars.status is True
    assert env_vars.IP_ADDRESS == "127.0.0.1"
    assert env_vars.PORT == 8888

    # Test con la variable IP_ADDRESS faltante
    with pytest.raises(EnvironmentVariableError):
        with monkeypatch.context() as m:
            m.delenv("IP_ADDRESS", raising=False)
            check_vars_environment()


# Test del runner de pylint con código válido
def test_run_pylint_valid_code():
    code = "def foo():\n    return 42\n"
    output = run_pylint(code)
    assert "Your code has been rated" in output


# Test del runner de pylint con código inválido
def test_run_pylint_invalid_code():
    code = "def foo(\n"
    output = run_pylint(code)
    assert "E0001" in output  # Pylint debería reportar un error de sintaxis


# Test de la interacción cliente-servidor
def test_client_server_interaction(monkeypatch):
    # Inicia el servidor en un hilo separado
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Crea un socket cliente para conectarse al servidor
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 8888))

    try:
        # Envía código Python al servidor
        code = "def foo():\n    return 42\n<<EOF>>"
        client_socket.sendall(code.encode('utf-8'))

        # Recibe la respuesta del servidor
        response = client_socket.recv(4096).decode('utf-8')
        assert "Your code has been rated" in response

    finally:
        client_socket.close()
        server_thread.join(timeout=1)
