import random
import time
from datetime import datetime

def generate_sensor_data():
    try:
        data = {
            "TDS": random.uniform(200, 1000),
            "Turbidity": random.uniform(0, 5), 
            "Chlorine": random.uniform(0, 2),   
            "pH": random.uniform(5, 9),         
            "Timestamp": datetime.now().isoformat()
        }
        return data

    except Exception as e:
        print(":: Error ::",e)
        raise

def water_params_loop():
    while True:
        data = generate_sensor_data()
        print(data)
        time.sleep(5)