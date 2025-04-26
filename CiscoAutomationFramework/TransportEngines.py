from CiscoAutomationFramework.Exceptions import AuthenticationException
from paramiko import SSHClient, AutoAddPolicy
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from time import sleep

default_command_end = '\n'
default_buffer = 100
default_timeout = 1
default_delay = .5
standard_prompt_endings = ('>', '#', '> ', '# ')


class BaseEngine(ABC):

    def __init__(self):
        self.hostname = ''
        self.prompt = None
        self.enable_password = None
        self.commands_sent_since_last_output_get = 0
        self.all_commands_sent = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def _extract_prompt(self, output):
        try:
            last_line_of_output = output[-1].strip()
        except IndexError:
            return
        for prompt_ending in standard_prompt_endings:
            if prompt_ending in last_line_of_output:
                self.prompt = f'{last_line_of_output.split(prompt_ending)[0]}{prompt_ending}'
                return

    def send_command(self, command, end=default_command_end):

        self.commands_sent_since_last_output_get += 1
        self.all_commands_sent.append(command)
        return self._send_command(command, end)

    def get_output(self, buffer_size=default_buffer, timeout=default_timeout, no_command_sent_previous=False):
        if no_command_sent_previous:
            self.commands_sent_since_last_output_get += 1

        output = ''
        for x in range(self.commands_sent_since_last_output_get):
            data = '\n'
            end = datetime.now() + timedelta(seconds=timeout)

            while not all([data.splitlines()[-1].startswith(self.hostname), any([x in data.splitlines()[-1] for x in standard_prompt_endings])]):
                from_device = self._get_output(buffer_size)
                if from_device:
                    data += from_device
                    end = datetime.now() + timedelta(seconds=timeout)
                else:
                    if datetime.now() > end:
                        break
                    sleep(.1)
            output += data[1:]

        self.commands_sent_since_last_output_get = 0

        if type(output) != list:
            output = output.splitlines()

        self._extract_prompt(output)

        return output

    def send_command_get_output(self, command, end=default_command_end, buffer_size=default_buffer, timeout=default_timeout, delay=default_delay):
        self.send_command(command, end)
        if delay:
            sleep(delay)
        return self.get_output(buffer_size, timeout)

    def send_command_get_truncated_output(self, command):
        self.send_command(command)
        output = []
        while True:
            for line in self.get_output(timeout=.1):
                output.append(line)

            if self.prompt in '\n'.join(output):
                break
            else:
                self.send_command(' ', end='')
        return output

    def _send_space_get_data(self, timeout=1):
        self._send_command('', end='\n')
        end = datetime.now() + timedelta(seconds=timeout)
        data = ''
        while not data.endswith(standard_prompt_endings):
            from_device = self._get_output(1000)
            if from_device:
                data += from_device
                end = datetime.now() + timedelta(seconds=timeout)
            else:
                sleep(.1)
                if datetime.now() >= end:
                    break
        return data

    def _prompt_lookup(self, output_data):
        prompt = None
        for line in reversed(output_data.splitlines()[-3:]):
            if len(line.split()) == 1 and any(x in line for x in standard_prompt_endings):
                prompt = line.strip().replace('\r\n', '')
                break
        if not prompt:
            return self._prompt_lookup(self._send_space_get_data())

        return prompt

    def _get_prompt_and_hostname(self):
        output = ''
        while not output.endswith(standard_prompt_endings):
            data = self._get_output(100)
            output += data
            if '% Authorization failed.' in output:
                raise AuthenticationException('% Authorization failed.')
        prompt = self._prompt_lookup(output)

        # prompt = data.splitlines()[-1].strip()
        hostname = prompt[:-1]
        return prompt, hostname

    @property
    def in_user_exec_mode(self) -> bool:
        if self.prompt.endswith('>'):
            return True
        return False

    @property
    def in_privileged_exec_mode(self) -> bool:
        if self.prompt.endswith('#') and not self.prompt.endswith(')#'):
            return True
        return False

    @property
    def in_configuration_mode(self) -> bool:
        if self.prompt.endswith(')#'):
            return True
        return False

    @abstractmethod
    def connect_to_server(self, ip, username, password, port) -> bool:
        pass

    @abstractmethod
    def _send_command(self, command, end) -> None:
        pass

    @abstractmethod
    def _get_output(self, buffer_size) -> str:
        pass

    @abstractmethod
    def close_connection(self) -> None:
        pass

class SSHEngine(BaseEngine):
    
    def __init__(self):
        super().__init__()
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.shell = None
        self.timeout = 10
        self._pre_jumphost_hostname = ''

    @property
    def _in_jumphost(self):
        return self._pre_jumphost_hostname != self.hostname
    
    def connect_to_server(self, ip, username, password, port):
        self.client.connect(
            hostname=ip,
            port=port,
            username=username,
            password=password,
            timeout=self.timeout
        )
        self.shell = self.client.invoke_shell()
        self.prompt, self.hostname = self._get_prompt_and_hostname()
        self._pre_jumphost_hostname = self.hostname

    def jumphost(self, ip, password, username=None, port=None, ssh_ver=None, vrf=None):
        command_string = 'ssh '
        if username:
            command_string += f'-l {username} '
        if port:
            command_string += f'-p {port} '
        if ssh_ver:
            command_string += f'-v {ssh_ver} '
        if vrf:
            command_string += f'-vrf {vrf} '
        command_string += ip

        self.send_command(command_string)
        sleep(0.3)
        _ = self._get_output(100)
        self.send_command(password)
        self.prompt, self.hostname = self._get_prompt_and_hostname()

    def exit_jumphost(self):
        if self._in_jumphost:
            self.send_command('exit')
            self.prompt, self.hostname = self._get_prompt_and_hostname()

    def _get_output(self, buffer_size):
        if self.shell.recv_ready():
            return bytes.decode(self.shell.recv(buffer_size))
        return ''
    
    def _send_command(self, command, end='\n'):
        self.shell.send(f'{command}{end}')

    def close_connection(self):
        self.exit_jumphost()
        self.client.close()
        