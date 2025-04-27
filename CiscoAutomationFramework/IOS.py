from CiscoAutomationFramework.FirmwareBase import CiscoFirmware
from time import sleep

class IOS(CiscoFirmware):

    @property
    def uptime(self):
        self.cli_to_privilaged_exec_mode()
        self.terminal_length('0')
        device_output = self.transport.send_command_get_output('show version')
        for line in device_output:
            if f'{self.transport.hostname.lower()} uptime' in line.lower():
                return ' '.join(line.split()[3:])
        return None
    
    @property
    def interfaces(self):
        self.cli_to_privilaged_exec_mode()
        self.terminal_length('0')
        raw_date = self.transport.send_command_get_output('show interfaces', buffer_size=500)
        try:
            parsed_data = []
            for line in raw_date[2:-2]:
                if not line.startswith(' '):
                    words = line.split()
                    interface_name = words[0]
                    parsed_data.append(interface_name)
        except IndexError as _:
            raise IndexError('Unexpected data from device, Unable to extract interface names from "show interfaces" command!')
        return parsed_data
    
    @property
    def mac_address_table(self):
        self.cli_to_privilaged_exec_mode
        self.terminal_length('0')
        return self.transport.send_command_get_output('show mac address-table')

    @property
    def arp_table(self):
        self.cli_to_privilaged_exec_mode()
        self.terminal_length('0')
        return self.transport.send_command_get_output('show ip arp')

    @property
    def running_config(self):
        self.cli_to_privilaged_exec_mode()
        self.terminal_length('0')
        running_config = self.transport.send_command_get_output('show running_confing', buffer_size=100)
        
        while True:
            enough_line = len(running_config) >= 4
            prompt_found = any(self.prompt in line for line in reversed (running_config[-4:]))
            if enough_line and prompt_found:
                break
            running_config += self.transport.get_output(buffer_size=100, no_command_sent_previous=True)
            sleep(0.1)
        config_body = running_config[2:-2]
        return '\n'.join(config_body)

    @property
    def startup_config(self):
        self.cli_to_privilaged_exec_mode()
        self.terminal_length('0')
        config = self.transport.send_command_get_output('show startup_config', buffer_size=100)

        while True:
            enough_line = len(config) >= 4
            prompt_found = any(self.prompt in line for line in reversed (config[-4:]))
            if enough_line and prompt_found:
                break
            config += self.transport.get_output(buffer_size=100, no_command_sent_previous=True)
            sleep(0.1)
        config_body = config[2:-2]
        return '\n'.join(config_body)
    
    def _terminal_length(self, n='0'):
        self.cli_to_privilaged_exec_mode()
        return self.transport.send_command_get_output(f'terminal length {n}')
    
    def _terminal_width(self, n='0'):
        self.cli_to_privilaged_exec_mode()
        return self.transport.send_command_get_output(f'terminal width {n}')
    
    def save_config(self):
        self.cli_to_privilaged_exec_mode()
        self.transport.send_command('copy running-config startup-config')
        data = self.transport.send_command_get_output('', timeout=15)
        if self.transport.prompt in ''.join(data[-1:]) and not any('%' in line for line in data):
            return True
        return False
    
    def add_local_user(self, username, password, password_code=0, *args, **kwargs):
        kwarg_string = ' '.join([f'{key} {value}' for key, value in kwargs.items()])
        command_string = f'username {username} {" ".join(args)} {kwarg_string} secret {password_code} {password}'
        self.cli_to_config_mode()
        return self.transport.send_command_get_output(command_string)

    def delete_local_user(self, username):
        self.cli_to_config_mode()
        self.transport.send_command(f'no username {username}')
        return self.transport.send_command_get_output('')