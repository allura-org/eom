from enum import Enum
import msgspec
from msgspec import Struct
from websocket import create_connection, WebSocket, WebSocketConnectionClosedException
import time
import logging
import socket
import threading

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
    ws: WebSocket = None
    _config: EdgeOMaticConfig = None
    _ip: str
    _port: int
    _lock: threading.Lock
    _reconnect_attempts: int = 0
    _max_reconnect_attempts: int = 3
    _last_connection_time: float = 0
    _connection_cooldown: float = 5.0  # seconds

    @staticmethod
    def send_and_recv_struct(ws: WebSocket, struct: Struct, wait_for_name: str|None=None, type=object):
        try:
            ws.send(msgspec.json.encode(struct))
            if wait_for_name:
                while True:
                    res = msgspec.json.decode(ws.recv(), type=object)
                    if wait_for_name in res:
                        return msgspec.convert(res[wait_for_name], type)
            return msgspec.json.decode(ws.recv(), type=type)
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error) as e:
            logging.error(f"WebSocket error during send_and_recv: {e}")
            raise
    
    @staticmethod
    def recv_struct(ws: WebSocket, wait_for_name: str|None=None, type=object):
        try:
            if wait_for_name:
                while True:
                    res = msgspec.json.decode(ws.recv(), type=object)
                    if wait_for_name in res:
                        return msgspec.convert(res[wait_for_name], type)
            return msgspec.json.decode(ws.recv(), type=type)
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error) as e:
            logging.error(f"WebSocket error during recv: {e}")
            raise
    
    def __init__(self, ip: str, port: int):
        self._ip = ip
        self._port = port
        self._lock = threading.Lock()
        self._connect()

    def _connect(self):
        """Establish connection to the device with retry logic"""
        if time.time() - self._last_connection_time < self._connection_cooldown:
            time.sleep(self._connection_cooldown)
        
        self._last_connection_time = time.time()
        self._reconnect_attempts = 0
        
        while self._reconnect_attempts < self._max_reconnect_attempts:
            try:
                logging.info(f"Connecting to EdgeOMatic at {self._ip}:{self._port} (attempt {self._reconnect_attempts + 1})")
                self.ws = create_connection(f"ws://{self._ip}:{self._port}/", timeout=10)
                
                # Start streaming readings
                self.send_and_recv_struct(self.ws, {
                    "streamReadings": None
                })
                
                # Get initial config
                self._config = self.send_and_recv_struct(self.ws, {
                    "configList": None
                }, wait_for_name="configList", type=EdgeOMaticConfig)
                
                logging.info(f"Successfully connected to EdgeOMatic")
                self._reconnect_attempts = 0
                return
            except (WebSocketConnectionClosedException, ConnectionResetError, socket.error) as e:
                self._reconnect_attempts += 1
                if self._reconnect_attempts >= self._max_reconnect_attempts:
                    logging.error(f"Failed to connect after {self._max_reconnect_attempts} attempts: {e}")
                    raise
                logging.warning(f"Connection attempt failed: {e}. Retrying in 2 seconds...")
                time.sleep(2)
    
    def _ensure_connection(self):
        """Ensure we have a valid connection before operations"""
        with self._lock:
            if self.ws is None:
                self._connect()
            return self.ws
    
    @property
    def config(self) -> EdgeOMaticConfig:
        self._ensure_connection()
        return self._config
    
    def set_config(self, config: EdgeOMaticConfig):
        self._ensure_connection()
        try:
            self._config = config
            return self.send_and_recv_struct(self.ws, {
                "configSet": dict(config)
            })
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error):
            # Try to reconnect once and retry
            self._connect()
            self._config = config
            return self.send_and_recv_struct(self.ws, {
                "configSet": dict(config)
            })

    def get_readings(self):
        self._ensure_connection()
        try:
            return self.recv_struct(self.ws, "readings", EdgeOMaticReadings)
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error):
            # Try to reconnect once and retry
            self._connect()
            return self.recv_struct(self.ws, "readings", EdgeOMaticReadings)
    
    def set_mode(self, mode: ControlMode):
        self._ensure_connection()
        try:
            return self.send_and_recv_struct(self.ws, {
                "setMode": mode.value
            }, "setMode")
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error):
            # Try to reconnect once and retry
            self._connect()
            return self.send_and_recv_struct(self.ws, {
                "setMode": mode.value
            }, "setMode")
    
    def set_motor_speed(self, speed: int):
        self._ensure_connection()
        try:
            return self.send_and_recv_struct(self.ws, {
                "setMotor": speed
            }, "setMotor")
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error):
            # Try to reconnect once and retry
            self._connect()
            return self.send_and_recv_struct(self.ws, {
                "setMotor": speed
            }, "setMotor")
    
    def restart(self):
        self._ensure_connection()
        try:
            result = self.send_and_recv_struct(self.ws, {
                "restart": None
            }, "restart")
            # Device is restarting, so our connection is likely gone
            self.close(force=True)
            return result
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error):
            # Connection already gone, just return success
            self.close(force=True)
            return {"success": True}
    
    def get_info(self):
        self._ensure_connection()
        try:
            return self.send_and_recv_struct(self.ws, {
                "info": None
            }, "info", EdgeOMaticInfo)
        except (WebSocketConnectionClosedException, ConnectionResetError, socket.error):
            # Try to reconnect once and retry
            self._connect()
            return self.send_and_recv_struct(self.ws, {
                "info": None
            }, "info", EdgeOMaticInfo)
    
    def close(self, force=False):
        """Close the connection and clean up resources"""
        if self.ws:
            try:
                if not force:
                    # Try a graceful close first
                    self.ws.close(timeout=1)
            except Exception as e:
                logging.warning(f"Error during connection close: {e}")
            finally:
                # Ensure resources are freed regardless of close success
                self.ws = None