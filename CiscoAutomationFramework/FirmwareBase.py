from CiscoAutomationFramework.TransportEngines import BaseEngine, default_buffer, default_timeout, default_command_end, default_delay
from CiscoAutomationFramework.Exceptions import EnablePasswordError
from abc import ABC, abstractmethod
from inspect import getmodule

class CiscoFirmware(ABC):
    def __init__(self, transport):
        if not isinstance(transport, BaseEngine):
            raise TypeError(f'transport object MUST be an instance of {getmodule(BaseEngine).__name__}.{BaseEngine.__name__}')
        self._terminal_length_value = None
        self._terminal_width_value = None
        self.transport = transport
        # self.terminal_length()

    @property
    def is_nexus(self) -> bool:
        return False
    
    @property
    def commands_send(self) -> list:
        return self.transport.all_commands_send
    
    def cli_to_config_mode(self) -> bool:
        if self.transport.in_user_exec_mode:
            self.cli_to_privileged_exec_mode()

        if self.transport.in_privileged_exec_mode:
            self.transport.send_command_get_output('config t')
        
        return self.transport.in_configuration_mode
    
    def cli_to_privileged_exec_mode(self) -> bool:
        if self.transport.in_privileged_exec_mode:
            return True
        if self.transport.in_configuration_mode:
            self.transport.send_command_get_output('end')
            return self.transport.in_privileged_exec_mode
        if self.transport.in_user_exec_mode:
            enabling_output = self.transport.send_command_get_output('enable')
            if self.transport.prompt not in enabling_output:
                if not self.transport.enable_password:
                    raise EnablePasswordError('No enable password provided, network device is asking for one!')
                self.transport.send_command_get_output(self.transport.enable_password)
                return self.transport.in_privileged_exec_mode
            
    @property
    def prompt(self) -> str:
        return self.transport.prompt
    
    @property
    def hostname(self) -> srt:
        return self.transport.hostname
    
    def send_command_get_output(self, command, end=default_command_end, buffer_size=default_buffer,
                                timeout=default_timeout, delay=default_delay) -> list:
        return self.transport.send_command_get_output(command, end, buffer_size, timeout, delay)
        
    def send_command(self, command, end=default_command_end) -> None:
        return self.transport.send_command(command, end)

    def get_output(self, buffer_size=default_buffer, timeout=default_timeout) -> list:
        return self.transport.get_output(buffer_size, timeout)
    
    def send_question_get_output(self, command) -> list:
        if command.endswith('?'):
            command = command.replace('?', '')
        question_output = self.send_command_get_output(command, end=' ?')

    def close_connection(self) -> None:
        return self.transport.close_connection()


    def terminal_length(self, n='0'):
        if self._terminal_length_value:
            if self._terminal_length_value != int(n):
                self._terminal_length_value = int(n)
                return self._terminal_length(n)
        else:
            self._terminal_length_value = int(n)
            return self._terminal_length(n)

    def terminal_width(self, n='0'):
        if self._terminal_width_value:
            if self._terminal_width_value != int(n):
                self._terminal_width_value = int(n)
                return self._terminal_width(n)
        else:
            self._terminal_width_value = int(n)
            return self._terminal_width(n)
        
    # Begin abstract properties

    @property
    @abstractmethod
    def uptime(slef) -> str:
        pass

    @property
    @abstractmethod
    def interfaces(self) -> list:
        pass

    @property
    @abstractmethod
    def mac_address_table(self) -> str:
        pass

    @property
    @abstractmethod
    def arp_table(self) -> str:
        pass

    @property
    @abstractmethod
    def running_config(self) -> str:
        pass

    @property
    @abstractmethod
    def startup_config(self) -> str:
        pass

    # Begin abstract methods

    @abstractmethod
    def _terminal_length(self, n='0'):
        pass

    @abstractmethod
    def _terminal_width(self, n='0'):
        pass

    @abstractmethod
    def save_config(self):
        pass

    @abstractmethod
    def add_local_user(self, username, password, password_code=0, *args, **kwargs):
        pass

    @abstractmethod
    def delete_local_user(self, username):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.transport.close_connection()