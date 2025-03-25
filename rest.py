from litestar import Litestar, get, post
from eom import EdgeOMatic

from litestar.datastructures import State
from litestar.di import Provide
from typing import Annotated, Dict, Any
from eom import EdgeOMaticConfig, ControlMode, EdgeOMaticReadings, EdgeOMaticInfo
import logging

eom: EdgeOMatic = EdgeOMatic("0.0.0.0", 80)

# Routes for EdgeOMatic API
@get("/config")
async def get_config() -> EdgeOMaticConfig:
    """Get the current EdgeOMatic configuration."""
    return eom.config

@post("/config")
async def set_config(
    data: EdgeOMaticConfig
) -> Dict[str, str]:
    """Update the EdgeOMatic configuration."""
    eom.set_config(data)
    return {"status": "success"}

@get("/readings")
async def get_readings() -> EdgeOMaticReadings:
    """Get the current EdgeOMatic readings."""
    return eom.get_readings()

@post("/mode/{mode:str}")
async def set_mode(
    mode: str
) -> Dict[str, Any]:
    """Set the EdgeOMatic control mode."""
    try:
        control_mode = ControlMode(mode)
        result = eom.set_mode(control_mode)
        return {"status": "success", "result": result}
    except ValueError:
        return {"status": "error", "message": f"Invalid mode: {mode}"}

@post("/motor/{speed:int}")
async def set_motor_speed(
    speed: int
) -> Dict[str, Any]:
    """Set the EdgeOMatic motor speed."""
    result = eom.set_motor_speed(speed)
    return {"status": "success", "result": result}

@post("/restart")
async def restart_device() -> Dict[str, Any]:
    """Restart the EdgeOMatic device."""
    result = eom.restart()
    return {"status": "success", "result": result}

@get("/info")
async def get_info() -> EdgeOMaticInfo:
    """Get information about the EdgeOMatic device."""
    return eom.get_info()

# Create a lifecycle hook to close the connection when the app shuts down
def on_shutdown() -> None:
    global eom
    if eom is not None:
        try:
            eom.restart()
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
        get_info
    ],
    on_shutdown=[on_shutdown]
)

