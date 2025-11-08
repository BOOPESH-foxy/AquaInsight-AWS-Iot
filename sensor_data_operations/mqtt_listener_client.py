import os
from sensor_data_operations.tank_metadata import district,tankId,village
from dotenv import load_dotenv

load_dotenv()

topic = f"water/quality/{district}/{village}/{tankId}/command"
