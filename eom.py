from enum import Enum
import msgspec
from msgspec import Struct
from websocket import create_connection, WebSocket

class ControlMode(Enum):
    Manual = "MANUAL_CONTROL"
    Automatic = "AUTOMAITC_CONTROL"
    Orgasm = "ORGASM_MODE"
    Unk = ""

class VibrationMode(Enum):
    GlobalSync = 0
    RampStop = 1
    Depletion = 2
    Enhancement = 3

class EdgeOMaticConfig(Struct):
    wifi_ssid: str
    wifi_key: str
    wifi_on: bool
    bt_display_name: str
    bt_on: bool
    force_bt_coex: bool
    led_brightness: int # originally `byte`
    websocket_port: int
    use_ssl: bool
    hostname: str
    motor_start_speed: int # originally `byte`
    motor_max_speed: int # originally `byte`
    motor_ramp_time_s: int
    edge_delay: int
    max_additional_delay: int
    minimum_on_time: int
    screen_dim_seconds: int
    screen_timeout_seconds: int
    reverse_menu_scroll: bool
    pressure_smoothing: int # originally `byte`
    classic_serial: bool
    sensitivity_threshold: int
    update_frequency_hz: int
    sensor_sensitivity: int # originally `byte`
    use_average_values: bool
    vibration_mode: VibrationMode
    use_post_orgasm: bool
    clench_pressure_sensitivity: int
    clench_time_to_orgasm_ms: int
    clench_detector_is_edging: bool = msgspec.field(name="clench_detector_in_edging") # ?????
    auto_edging_duration_minutes: int
    post_orgasm_duration_seconds: int
    edge_menu_lock: bool
    post_orgasm_menu_lock: bool
    max_clench_duration_ms: int
    clench_time_threshold_ms: int
    # added in version 2?
    _filename: str
    store_command_history: bool
    console_basic_mode: bool
    enable_screensaver: bool
    language_file_name: str
    remote_update_url: str
    version: int = msgspec.field(name="$version")

class EdgeOMaticReadings(Struct):
    pressure: int
    pavg: int
    motor: int
    arousal: int
    millis: int
    run_mode: ControlMode = msgspec.field(name="runMode")
    permit_orgasm: bool = msgspec.field(name="permitOrgasm")
    post_orgasm: bool = msgspec.field(name="postOrgasm")
    lock: bool

class EdgeOMaticInfo(Struct):
    device: str
    serial: str
    hw_version: str = msgspec.field(name="hwVersion")
    fw_version: str = msgspec.field(name="fwVersion")

class EdgeOMatic:
    ws: WebSocket
    _config: EdgeOMaticConfig

    @staticmethod
    def send_and_recv_struct(ws: WebSocket, struct: Struct, wait_for_name: str|None=None, type=object):
        ws.send(msgspec.json.encode(struct))
        if wait_for_name:
            while True:
                res = msgspec.json.decode(ws.recv(), type=object)
                if wait_for_name in res:
                    return msgspec.convert(res[wait_for_name], type)
        return msgspec.json.decode(ws.recv(), type=type)
    
    @staticmethod
    def recv_struct(ws: WebSocket, wait_for_name: str|None=None, type=object):
        if wait_for_name:
            while True:
                res = msgspec.json.decode(ws.recv(), type=object)
                if wait_for_name in res:
                    return msgspec.convert(res[wait_for_name], type)
        return msgspec.json.decode(ws.recv(), type=type)
    
    def __init__(self, ip: str, port: int):
        self.ws = create_connection(f"ws://{ip}:{port}/")
        self.send_and_recv_struct(self.ws, {
            "streamReadings": None
        })
        self._config = self.send_and_recv_struct(self.ws, {
            "configList": None
        }, wait_for_name="configList", type=EdgeOMaticConfig)

    @property
    def config(self) -> EdgeOMaticConfig:
        return self._config
    
    def set_config(self, config: EdgeOMaticConfig):
        self._config = config
        self.send_and_recv_struct(self.ws, {
            "configSet": dict(config)
        })

    def get_readings(self):
        return self.recv_struct(self.ws, "readings", EdgeOMaticReadings)
    
    def set_mode(self, mode: ControlMode):
        return self.send_and_recv_struct(self.ws, {
            "setMode": mode.value
        }, "setMode")
    
    def set_motor_speed(self, speed: int):
        return self.send_and_recv_struct(self.ws, {
            "setMotor": speed
        }, "setMotor")
    
    def restart(self):
        return self.send_and_recv_struct(self.ws, {
            "restart": None
        }, "restart")
    
    def get_info(self):
        return self.send_and_recv_struct(self.ws, {
            "info": None
        }, "info", EdgeOMaticInfo)
    
    def close(self):
        self.ws.close(timeout=None)