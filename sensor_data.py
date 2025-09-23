import random
import time
from datetime import datetime

def generate_sensor_data():
    data = {
        "TDS": random.uniform(200, 1000),
        "Turbidity": random.uniform(0, 5), 
        "Chlorine": random.uniform(0, 2),   
        "pH": random.uniform(5, 9),         
        "Timestamp": datetime.now().isoformat()
    }
    print(data)

while True:
    generate_sensor_data()
    time.sleep(5)