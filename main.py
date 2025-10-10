from aws_iot_thing import create_aws_thing,publish_sensor_data
import typer

app = typer.Typer(help="AWS IoT thing data processing - sensor")

@app.command("create_thing")
def create_aws_thing_typer():
    """Create AWS thing on the specified region"""
    create_aws_thing()

@app.command("publish_data")
def publish_sensor_data_typer():
    """Starts publishing the sensor data to AWS IoT thing"""
    publish_sensor_data()

if __name__ == "__main__":
    app()