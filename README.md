# EdgeOMatic Control API

A Python-based REST API for controlling and monitoring EdgeOMatic devices via WebSockets.

## 🚀 Features

- Complete WebSocket communication with EdgeOMatic devices
- RESTful API endpoints for device control
- Configuration management
- Real-time readings and monitoring
- Multiple control modes (Manual, Automatic, Orgasm)
- Device information retrieval

## 📋 Requirements

- Python 3.7+
- `msgspec` library
- `websocket-client` library
- `litestar` web framework

## 🔧 Installation

```bash
# Install dependencies
uv pip install msgspec websocket-client litestar granian

# Run the API
granian rest:app --interface asgi
```

## Known Issues
- Sometimes the device's display will freeze, not responding to button presses, while the server is running. Sending a Restart request usually works to solve this. It's unknown as of yet whether the device continues to function while the display is frozen.
- On repeated starts and stops of the server, the device will simply stop accepting connections. The cause is as of yet unknown but we suspect limitations with the ESP32 radio. If this occurs, unplug the device, plug it back in, and wait a few minutes; it will initially fail to connect to WiFi but this will resolve itself.

## 🚀 Quick Start

1. Configure your EdgeOMatic device IP and port in `rest.py`:

```python
eom: EdgeOMatic = EdgeOMatic("your_device_ip", your_device_port)
```

2. Start the API server:

```bash
litestar run --app rest:app --host 0.0.0.0 --port 8000
```

3. Access the API at `http://localhost:8000`

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/config` | GET | Retrieve current device configuration |
| `/config` | POST | Update device configuration |
| `/readings` | GET | Get real-time device readings |
| `/mode/{mode}` | POST | Set the control mode (MANUAL_CONTROL, AUTOMAITC_CONTROL, ORGASM_MODE) |
| `/motor/{speed}` | POST | Set the motor speed (0-255) |
| `/restart` | POST | Restart the device |
| `/info` | GET | Get device information |

## 💡 Usage Examples

### Get Device Configuration

```bash
curl http://localhost:8000/config
```

### Update Configuration

```bash
curl -X POST http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"motor_max_speed": 200, "sensitivity_threshold": 50, ...}'
```

### Get Current Readings

```bash
curl http://localhost:8000/readings
```

### Set Control Mode

```bash
curl -X POST http://localhost:8000/mode/XXX
```

### Set Motor Speed

```bash
curl -X POST http://localhost:8000/motor/XXX
```

## 🧠 Core Components

### EdgeOMatic Class

The `EdgeOMatic` class in `eom.py` provides the foundation for device communication:

- WebSocket connection management
- Configuration retrieval and updates
- Real-time readings
- Control mode selection
- Motor speed control

### REST API

Built with Litestar, the API in `rest.py` offers a user-friendly interface to interact with the device from any HTTP client.

## ⚠️ Important Notes

- This API is intended for controlling EdgeOMatic devices on a secure, private network.
- Always ensure proper device cleaning and maintenance according to the manufacturer's instructions.

---

*This project is not affiliated with EdgeOMatic's manufacturer and is provided as-is without warranty.*
