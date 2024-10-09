# pytest/test_pylint_service.py

import os
import pytest
import socket
import threading
from unittest import mock
from unittest.mock import MagicMock, patch

# Ajustamos el import según la estructura de directorios
from pylint_service.pylint_service import check_vars_environment, run_pylint, handle_client

def test_check_vars_environment_valid(monkeypatch):
    # Configura variables de entorno válidas
    monkeypatch.setenv('IP_ADDRESS', '127.0.0.1')
    monkeypatch.setenv('PORT', '8000')
    result = check_vars_environment()
    assert result.status == True
    assert result.IP_ADDRESS == '127.0.0.1'
    assert result.PORT == 8000

def test_check_vars_environment_missing_ip(monkeypatch):
    # Elimina IP_ADDRESS para simular que falta
    monkeypatch.delenv('IP_ADDRESS', raising=False)
    monkeypatch.setenv('PORT', '8000')
    result = check_vars_environment()
    assert result.status == False
    assert result.IP_ADDRESS == '0.0.0.0'
    assert result.PORT == 5000

def test_check_vars_environment_invalid_port(monkeypatch):
    # Establece un PORT inválido
    monkeypatch.setenv('IP_ADDRESS', '127.0.0.1')
    monkeypatch.setenv('PORT', '-1')
    result = check_vars_environment()
    assert result.status == False
    assert result.IP_ADDRESS == '0.0.0.0'
    assert result.PORT == 5000

def test_run_pylint_with_valid_code():
    # Código Python válido
    code = "def add(a, b):\n    return a + b\n"
    output = run_pylint(code)
    assert "Your code has been rated at" in output

def test_run_pylint_with_invalid_code():
    # Código Python con errores de sintaxis
    code = "def add(a,b):\nreturn a + b\n"
    output = run_pylint(code)
    assert "syntax-error" in output or "expected an indented block" in output

def test_run_pylint_with_empty_code():
    # Código vacío
    code = ""
    output = run_pylint(code)
    assert "Your code has been rated at" in output

@patch('pylint_service.pylint_service.run_pylint')
def test_handle_client(mock_run_pylint):
    # Simula el comportamiento de run_pylint
    mock_run_pylint.return_value = "Pylint analysis result"
    
    # Crea un socket de cliente simulado
    client_socket = mock.MagicMock()
    addr = ('127.0.0.1', 12345)

    # Simula los datos recibidos del cliente
    code = "def add(a, b):\n    return a + b\n"
    data = code + '<<EOF>>'
    client_socket.recv.return_value = data.encode('utf-8')

    # Ejecuta la función handle_client
    handle_client(client_socket, addr)

    # Verifica que sendall fue llamado con los datos correctos
    calls = client_socket.sendall.call_args_list
    assert b"Analyzing file... " in calls[0][0][0]
    assert b"Pylint analysis result" in calls[1][0][0]

