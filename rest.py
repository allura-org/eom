from litestar import Litestar, get, post
from eom import EdgeOMatic

from litestar.datastructures import State
from litestar.di import Provide
from typing import Annotated, Dict, Any
from eom import EdgeOMaticConfig, ControlMode, EdgeOMaticReadings, EdgeOMaticInfo
import logging
import os
import signal
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get connection details from environment variables if available
dev_addr = os.environ.get("EOM_DEV_ADDR", "0.0.0.0")
dev_port = int(os.environ.get("EOM_DEV_PORT", "80"))

# Connection management
eom: EdgeOMatic = None
eom_lock = threading.Lock()

def get_eom_instance():
    """Get or create the singleton EdgeOMatic instance"""
    global eom
    if eom is None:
        with eom_lock:
            if eom is None:
                try:
                    logging.info(f"Creating EdgeOMatic connection to {dev_addr}:{dev_port}")
                    eom = EdgeOMatic(dev_addr, dev_port)
                except Exception as e:
                    logging.error(f"Failed to connect to EdgeOMatic: {e}")
                    raise
    return eom

# Create initial connection
try:
    eom = get_eom_instance()
except Exception as e:
    logging.error(f"Initial connection failed: {e}")
    # We'll try again when the first request comes in

# Routes for EdgeOMatic API
@get("/config")
async def get_config() -> EdgeOMaticConfig:
    """Get the current EdgeOMatic configuration."""
    return get_eom_instance().config

@post("/config")
async def set_config(
    data: EdgeOMaticConfig
) -> Dict[str, str]:
    """Update the EdgeOMatic configuration."""
    get_eom_instance().set_config(data)
    return {"status": "success"}

@get("/readings")
async def get_readings() -> EdgeOMaticReadings:
    """Get the current EdgeOMatic readings."""
    return get_eom_instance().get_readings()

@post("/mode/{mode:str}")
async def set_mode(
    mode: str
) -> Dict[str, Any]:
    """Set the EdgeOMatic control mode."""
    try:
        control_mode = ControlMode(mode)
        result = get_eom_instance().set_mode(control_mode)
        return {"status": "success", "result": result}
    except ValueError:
        return {"status": "error", "message": f"Invalid mode: {mode}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@post("/motor/{speed:int}")
async def set_motor_speed(
    speed: int
) -> Dict[str, Any]:
    """Set the EdgeOMatic motor speed."""
    try:
        result = get_eom_instance().set_motor_speed(speed)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@post("/restart")
async def restart_device() -> Dict[str, Any]:
    """Restart the EdgeOMatic device."""
    global eom
    try:
        result = get_eom_instance().restart()
        # After restart, clear our instance so we create a new one on next request
        with eom_lock:
            eom = None
        return {"status": "success", "result": result}
    except Exception as e:
        # Also clear instance on error
        with eom_lock:
            eom = None
        return {"status": "error", "message": str(e)}

@get("/info")
async def get_info() -> EdgeOMaticInfo:
    """Get information about the EdgeOMatic device."""
    return get_eom_instance().get_info()

# Health check endpoint
@get("/health")
async def health_check() -> Dict[str, Any]:
    """Check if the connection to EdgeOMatic is healthy."""
    global eom
    try:
        # Try to get info as a health check
        if eom is not None:
            info = eom.get_info()
            return {
                "status": "healthy",
                "device": info.device,
                "firmware": info.fw_version
            }
        else:
            # Try to establish a connection
            instance = get_eom_instance()
            info = instance.get_info()
            return {
                "status": "healthy",
                "device": info.device,
                "firmware": info.fw_version,
                "note": "Connection was re-established"
            }
    except Exception as e:
        # Reset the connection for next attempt
        with eom_lock:
            if eom is not None:
                try:
                    eom.close(force=True)
                except:
                    pass
                eom = None
        
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Create a lifecycle hook to close the connection when the app shuts down
def on_shutdown() -> None:
    global eom
    if eom is not None:
        logging.info("Closing connection to EdgeOMatic...")
        try:
            # Force close the connection
            eom.close(force=True)
            eom = None
            logging.info("Connection closed successfully")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

# App configuration
app = Litestar(
    route_handlers=[
        get_config, 
        set_config, 
        get_readings, 
        set_mode, 
        set_motor_speed, 
        restart_device, 
        get_info,
        health_check
    ],
    on_shutdown=[on_shutdown]
)

