"""SSH helper for NFQWS Keenetic integration."""
from __future__ import annotations

import logging
import paramiko
import socket
from typing import Tuple

_LOGGER = logging.getLogger(__name__)

class SSHHelper:
    """SSH connection helper class."""

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        """Initialize SSH helper."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._ssh = None

    def connect(self) -> bool:
        """Establish SSH connection."""
        try:
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            _LOGGER.debug("Connecting to %s:%s as %s", self.host, self.port, self.username)
            
            self._ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=15,
                banner_timeout=30,
                auth_timeout=15,
            )
            
            # Test connection with a simple command
            stdin, stdout, stderr = self._ssh.exec_command("echo connected", timeout=10)
            output = stdout.read().decode().strip()
            
            if output == "connected":
                _LOGGER.debug("SSH connection established successfully")
                return True
            else:
                _LOGGER.error("SSH connection test failed")
                return False
                
        except paramiko.AuthenticationException:
            _LOGGER.error("SSH authentication failed for user %s", self.username)
            return False
        except paramiko.SSHException as err:
            _LOGGER.error("SSH error: %s", err)
            return False
        except socket.timeout:
            _LOGGER.error("SSH connection timeout to %s:%s", self.host, self.port)
            return False
        except socket.error as err:
            _LOGGER.error("Socket error connecting to %s:%s: %s", self.host, self.port, err)
            return False
        except Exception as err:
            _LOGGER.error("Unexpected SSH error: %s", err)
            return False

    def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str]:
        """Execute command via SSH."""
        stdout_data, stderr_data = "", ""
        
        if not self._ssh or not self.is_connected:
            if not self.connect():
                return "", "SSH connection failed"
        
        try:
            _LOGGER.debug("Executing command: %s", command)
            stdin, stdout, stderr = self._ssh.exec_command(command, timeout=timeout)
            stdout_data = stdout.read().decode().strip()
            stderr_data = stderr.read().decode().strip()
            
            if stderr_data:
                _LOGGER.debug("Command stderr: %s", stderr_data)
            if stdout_data:
                _LOGGER.debug("Command stdout: %s", stdout_data)
                
        except paramiko.SSHException as err:
            _LOGGER.error("SSH command error: %s", err)
            stderr_data = str(err)
        except socket.timeout:
            _LOGGER.error("SSH command timeout")
            stderr_data = "Command timeout"
        except Exception as err:
            _LOGGER.error("Unexpected command error: %s", err)
            stderr_data = str(err)
        
        return stdout_data, stderr_data

    @property
    def is_connected(self) -> bool:
        """Check if SSH connection is active."""
        if not self._ssh:
            return False
        try:
            transport = self._ssh.get_transport()
            return transport and transport.is_active()
        except Exception:
            return False

    def disconnect(self) -> None:
        """Close SSH connection."""
        if self._ssh:
            try:
                self._ssh.close()
            except Exception as err:
                _LOGGER.debug("Error closing SSH connection: %s", err)
            finally:
                self._ssh = None

    def __del__(self) -> None:
        """Destructor to ensure connection is closed."""
        self.disconnect()