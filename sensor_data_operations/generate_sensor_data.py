import random
from tank_metadata import tankId,village,district

def generate_sensor_data():
    try:
        data = {
            "tankId": tankId,
            "village": village,
            "district": district,
            "TDS": random.uniform(200, 1000),
            "Turbidity": random.uniform(0, 5), 
            "Chlorine": random.uniform(0, 2),   
            "pH": random.uniform(5, 9),         
        }
        return data

    except Exception as e:
        print(":: Error ::",e)
        raise
