import os
import json
from dotenv import load_dotenv
from sensor_data_operations.tank_metadata import topic

load_dotenv()

def response_message_processor(payload):
    """Process incoming MQTT messages from IoT Core"""
    try:
        data = json.loads(payload.decode("utf-8"))
        print("📨 Received command from ECS:")
        print("  Payload:", json.dumps(data, indent=2))
        
        cl_actions = data.get("command")
        if cl_actions == "Dispense Cl":
            print("🔧 Action: Dispensing Chlorine")
        elif cl_actions == "No-changes":
            print("Action: No changes needed")
        else:
            print(f"Unknown command: {cl_actions}")
            
    except json.JSONDecodeError:
        print("Raw payload (not JSON):", payload)
    except Exception as e:
        print(f"Error processing message: {e}")


def topic_listener():
    """Listen to IoT topic for commands from ECS containers"""
    print("🎧 Starting MQTT topic listener...")
    print(f"📡 Listening to topic: {topic}")
    print("⚠️  Note: This is a placeholder implementation.")
    print("   For full MQTT functionality, you need to:")
    print("   1. Install awsiotsdk: pip install awsiotsdk")
    print("   2. Configure IoT certificates")
    print("   3. Implement actual MQTT connection")
    print("\n🔄 Simulating listener (press Ctrl+C to stop)...")
    
    try:
        import time
        while True:
            # Simulate receiving a message every 30 seconds
            time.sleep(30)
            print("💭 Simulated message received...")
            sample_payload = json.dumps({
                "command": "No-changes",
                "timestamp": int(time.time()),
                "source": "ECS-container"
            }).encode('utf-8')
            response_message_processor(sample_payload)
            
    except KeyboardInterrupt:
        print("\n🛑 MQTT listener stopped by user")
    except Exception as e:
        print(f"❌ MQTT listener error: {e}")