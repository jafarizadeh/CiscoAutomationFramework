from threading import Thread
from CiscoAutomationFramework import connect_ssh
from CiscoAutomationFramework.FirmwareBase import CiscoFirmware
from abc import ABC, abstractmethod

class SSH(Thread, ABC):

    def __init__(self, ip, username, password, enable_password=None, perform_secondary_action=False, **kwargs):

        super().__init__()
        self.ip = ip
        self.username = username
        self.password = password
        self.enable_password = enable_password
        self.perform_secondary_action = perform_secondary_action
        self.hostname = ''
        self.commands_sent = []
        self.is_nexus = False

    def during_login(self, ssh):
        pass

    def secondary_action(self, ssh):
        pass

    def post_secondary_action(self, ssh):
        pass

    def run(self) -> None:

        with connect_ssh(self.ip, self.username, self.password, enable_password=self.enable_password) as ssh:
            self.is_nexus = ssh.is_nexus
            self.hostname = ssh.hostname
            self.during_login(ssh)
            if self.perform_secondary_action:
                self.secondary_action(ssh)
                self.post_secondary_action(ssh)
            self.commands_sent = ssh.commands_sent


class SSHSplitDeviceType(SSH):

    @abstractmethod
    def ios_during_login(self, ssh):
        pass

    @abstractmethod
    def nexus_during_login(self, ssh):
        pass

    @abstractmethod
    def ios_secondary_action(self, ssh):
        pass

    @abstractmethod
    def nexus_secondary_action(self, ssh):
        pass

    @abstractmethod
    def ios_post_secondary_action(self, ssh):
        pass

    @abstractmethod
    def nexus_post_secondary_action(self, ssh):
        pass

    def during_login(self, ssh):
        if self.is_nexus:
            self.nexus_during_login(ssh)
        else:
            self.ios_during_login(ssh)

    def secondary_action(self, ssh):
        if self.is_nexus:
            self.secondary_action(ssh)
        else:
            self.secondary_action(ssh)
            pass

    def post_secondary_action(self, ssh):
        if self.is_nexus:
            self.nexus_post_secondary_action(ssh)
        else:
            self.ios_post_secondary_action(ssh)


def start_threads(object, ips, username, password, enable_password=None,
                  perform_secondary_action=False, wait_for_threads=False, **kwargs):

    if not issubclass(object, SSH):
        raise TypeError('object MUST be a subclass of ThreadedSSH!')

    threads = [object(ip=ip, username=username, password=password, enable_password=enable_password,
                      perform_secondary_action=perform_secondary_action, **kwargs) for ip in ips]
    for thread in threads:
        thread.start()

    if wait_for_threads:
        for thread in threads:
            thread.join()

    return threads