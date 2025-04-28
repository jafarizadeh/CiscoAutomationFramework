from CiscoAutomationFramework.TransportEngines import SSHEngine
from CiscoAutomationFramework.FirmwareDetect import detect_firmware
from CiscoAutomationFramework.FirmwareBase import CiscoFirmware

def connect_ssh(ip, username, password, port=22, enable_password=None, timeout=10) -> CiscoFirmware:
    engine = SSHEngine()
    engine.enable_password = enable_password
    engine.timeout = timeout
    engine.connect_to_server(ip, username, password, port)
    firmware = detect_firmware(engine)
    return firmware
