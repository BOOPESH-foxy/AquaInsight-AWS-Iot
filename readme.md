# Water Quality Monitoring with AWS IoT and Timestream

This repository contains a Python-based solution for simulating and managing water quality data. The project focuses on monitoring various parameters like TDS (Total Dissolved Solids), turbidity, chlorine, and pH levels using sensors and sending the data to AWS IoT for processing. The data is then stored in AWS Timestream for time-series analytics and processing.

## Project Overview

The main components of the project include:
1. **Sensor Data Generation**: Python code that simulates sensor data (TDS, turbidity, chlorine, and pH levels).
2. **AWS IoT Integration**: Sending the sensor data to AWS IoT for further processing.
3. **Data Storage in AWS Timestream**: Storing the data in AWS Timestream for time-series analysis.

## Project Structure

The repository contains the following files:

- **generate_sensor_data.py**: A Python script that generates random values for TDS, turbidity, chlorine, and pH, and sends the data to AWS IoT and AWS Timestream.
- **iot_integration.py**: A Python script for handling the interaction with AWS IoT.
- **timestream_integration.py**: A Python script for sending data to AWS Timestream.

## Setup

### Prerequisites

- Python 3.x
- AWS CLI configured with the appropriate access keys.
- Boto3 library installed.

To install the necessary Python libraries, run the following command:

```bash
pip install boto3
