from device_driver.laser_driver import LaserDriver
from fastapi import Request

def get_laser_driver(request: Request) -> LaserDriver:
    return request.app.state.laser_driver

