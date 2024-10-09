# ../app/pylint_service.py
# This script contains the logic for the listen service using sockets
"""
Service that runs Pylint on Python code and returns the result.

This script sets up a server that listens for incoming connections using sockets.
When a client connects and sends Python code (ending with a specified delimiter), the server
runs Pylint on the received code and sends back the analysis results to the client.

Environment variables:
    IP_ADDRESS: The server's IP address to bind to (default '0.0.0.0')
    PORT: The server's port to listen on (default 5000)

Functions:
    check_vars_environment():
        Checks and retrieves the IP_ADDRESS and PORT from the environment variables.
    run_pylint(file_content):
        Runs Pylint on the given Python code and returns the output.
    handle_client(client_socket, addr):
        Handles a client's connection, receives code, runs Pylint, and sends back the result.
    start_server():
        Starts the server and begins listening for incoming connections.

Usage:
    - Run this script to start the server.
    - Connect to the server and send Python code (ending with '<<EOF>>') to be analyzed by Pylint.
    - Receive the Pylint analysis results from the server.
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
FORMAT_STR= '%(asctime)s - %(levelname)s - %(funcName)s - %(lineno)d - %(message)s'
parameters = {
    'level' : logging.INFO,
    'format' : FORMAT_STR,
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
    Checks and validates the IP_ADDRESS and PORT environment variables.

    If the variables are missing or invalid, default values are used.

    Returns:
        StatusEnvironmentVariable: An object containing the status, PORT,
            and IP_ADDRESS.
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
        logging.warning('Error at check_vars_environment %s', error, exc_info=True)
        return StatusEnvironmentVariable(status=False, PORT=5000, IP_ADDRESS='0.0.0.0')

# run_pylint
def run_pylint(file_content: str) -> str:
    """
    Runs Pylint on a temporary file with the provided content.

    Args:
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
            capture_output=True, text=True
        )

        # Check if pylint encountered any errors
        if result.returncode != 0:
            logging.error("Error running pylint: %s", result.stderr)
            return result.stderr

        # Return Pylint's output (plain text)
        return result.stdout
    except subprocess.CalledProcessError as error:
        logging.error("Error running Pylint: %s", error, exc_info=True)
        return f"Error running Pylint: {error}"
    finally:
        # Delete the temporary file if it was created
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# handle_client
def handle_client(client_socket, addr) -> None:
    """
    Handles a client's connection, receives Python code, runs Pylint,
    and sends back the result.

    Receives data from the client until the specified delimiter ('<<EOF>>')
    is encountered. Runs Pylint on the received code and sends the output
    back to the client.

    Args:
        client_socket (socket.socket): The socket object representing the
            client connection.
        addr (tuple): The address of the connected client.
    """
    try:
        logging.info('Connection from %s' ,addr)

        delimiter = '<<EOF>>'
        buffer = ''

        # Receive the file name and content from the client
        while delimiter not in buffer:
            data =  client_socket.recv(4096).decode('utf-8')
            if not data:
                break
            buffer += data

        # clean delimiter
        file_content = buffer.replace(delimiter, '')
        # run_pylint call
        pylint_output = run_pylint(file_content)
        # Send a message to client
        client_socket.sendall(b"Analyzing file... ")
        logging.info('Running Pylint on file %s')
        # Run Pylint on the received file
        pylint_output = run_pylint(file_content)
        # Send Pylint's output back to the client (plain text)
        client_socket.sendall(pylint_output.encode())
    except socket.error as error:
        logging.error('Error handling connection : %s', error, exc_info=True)
        client_socket.sendall(f"Server error: {error}".encode())
    finally:
        client_socket.close()
        logging.info("Connection closed.")

# start_server
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
