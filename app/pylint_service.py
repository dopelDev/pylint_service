# ../app/pylint_service.py
# This script contains the logic for the listen service using sockets
"""
Service that runs Pylint on Python files and returns the result.

This script uses sockets to listen for incoming connections, receive Python files and their content,
and execute Pylint on them. The result is sent back to the client.

Environment variables:
    IP_ADDRESS: the server's IP address (default 0.0.0.0)
    PORT: the server's port (default 5634)

Functions:
    run_pylint(file_name, file_content):
    Runs Pylint on a temporary file with the provided content
        and returns Pylint's standard output as plain text.
    start_server(): starts the server and begins listening for incoming connections.

Usage:
    - Run this script to start the server.
    - Send a request to the server with the file name
        and its content to execute Pylint on it.
"""

import socket
import subprocess
import os
import logging
import tempfile
import threading
from typing import NamedTuple
from dotenv import load_dotenv

# Load environment variables from config.env
load_dotenv('config.env')

# Configure the logger
# Parameters for logging
parameters = {
    'level' : logging.INFO,
    'format' : '%(asctime)s - %(levelname)s - %(message)s',
    'filename' : 'pylint_service.log'
}
logging.basicConfig(**parameters)

# Environment variables Error class
class EnvironmentVariableError(Exception):
    """
    Raised when an environment variable is not set or has an invalid value.
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

# class StatusEnvironmentVariable is a outgoing from check_vars_environment
class StatusEnvironmentVariable(NamedTuple):
    """
    StatusEnvironmentVariable is a structured representation of environment 
    variable details in a server environment.

    Attributes:
    -----------
    status : bool
        Indicates whether the environment variable is active (True) or inactive (False).
    PORT : int
        The port number on which the service is running.
    IP_ADDRESS : str
        The IP address associated with the environment variable.
    """
    status : bool
    PORT : int
    IP_ADDRESS : str

# check_vars_environment
def check_vars_environment() -> StatusEnvironmentVariable:
    """
    Check Vars Environment from config.env
    Default Vars:
        IP_ADDRESS=0.0.0.0
        PORT=5634
    Args:
        IP_ADDRESS (str): The IP address environment variable.
        PORT (int): The port number environment variable.
    Returns:
        bool: Whether the environment variables are set and valid.
    """
    try:
        ip_address = os.getenv('IP_ADDRESS')
        port = os.getenv('PORT')
        if ip_address is None or not ip_address.split():
            raise EnvironmentVariableError(f"Missing or invalid IP_ADDRESS {ip_address}")
        if port is None or not port.isdigit() or int(port) <= 0:
            raise EnvironmentVariableError(f'Missing or invalid PORT {port}')
        return StatusEnvironmentVariable(status=True, PORT=int(port), IP_ADDRESS=ip_address)

    except (EnvironmentVariableError, ValueError) as error:
        logging.warning(f'Error at check_vars_environment {error}')
        return StatusEnvironmentVariable(status=False, PORT=5634, IP_ADDRESS='0.0.0.0')

# run_pylint
def run_pylint(file_name: str, file_content: str) -> str:
    """
    Runs Pylint on a temporary file with the provided content.

    Args:
        file_name (str): Name of the file to be analyzed.
        file_content (str): Content of the file to be analyzed.

    Returns:
        str: Pylint's standard output as plain text.
    """
    temp_file_path = ''
    try:
        # Create a temporary file securely
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_file.write(file_content.encode('utf-8'))
            temp_file_path = temp_file.name

        # Run pylint on the temporary file and capture the standard output
        result = subprocess.run(
            ["pylint", temp_file_path],
            capture_output=True, text=True, check=True
        )

        # Check if pylint encountered any errors
        if result.returncode != 0:
            logging.error(f"Error running pylint: {result.stderr}")
            return result.stderr

        # Return Pylint's output (plain text)
        return result.stdout
    except Exception as error:
        logging.error(f"Error running Pylint: {error}")
        return f"Error running Pylint: {error}"
    finally:
        # Delete the temporary file if it was created
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# handle_client
def handle_client(client_socket, addr) -> None:
    """
    Handles a client's connection, receives the file, and runs Pylint.

    Args:
        client_socket (socket): Client socket.
        addr (tuple): Client address.
    """
    try:
        logging.info(f"Connection from {addr}")

        # Receive the file name and content from the client
        file_name = client_socket.recv(1024).decode().strip()
        file_content = ""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            file_content += data.decode()

        logging.info(f"Running Pylint on file {file_name}")

        # Run Pylint on the received file
        pylint_output = run_pylint(file_name, file_content)

        # Send Pylint's output back to the client (plain text)
        client_socket.sendall(pylint_output.encode())
    except Exception as error:
        logging.error(f"Error handling connection: {error}")
        client_socket.sendall(f"Server error: {error}".encode())
    finally:
        client_socket.close()
        logging.info("Connection closed.")

def start_server() -> None:
    """
    Starts the server and begins listening for incoming connections.

    Reads the IP and port from the environment variables, sets up the server socket,
    and begins listening for incoming connections. When a connection is received,
    runs Pylint on the received file and sends the output back to the client.
    """
    # Ensure the values are being read from the environment variables in config.env
    env_vars = check_vars_environment()

    # Set up the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((env_vars.IP_ADDRESS, env_vars.PORT))
    server_socket.listen(5)

    logging.info(f"Pylint server running at {env_vars.IP_ADDRESS}:{env_vars.PORT}...")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr)).start()
    except KeyboardInterrupt:
        logging.info("Server stopped manually.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
