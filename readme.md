# Water Quality Monitoring with AWS IoT and Timestream

This repository contains a Python-based solution for simulating and managing water quality data. The project focuses on monitoring various parameters like TDS (Total Dissolved Solids), turbidity, chlorine, and pH levels using sensors and sending the data to AWS IoT for processing. The data is then stored in AWS Timestream for time-series analytics and processing.

## Project Status - Under Development

## Project Overview

The main components of the project include:
1. **Sensor Data Generation**: Python code that simulates sensor data (TDS, turbidity, chlorine, and pH levels).
2. **AWS IoT Integration**: Sending the sensor data to AWS IoT for further processing.
3. **IoT rule**: Routes the sensor data to other AWS resources.
4. **AWS SQS**: To queue the messages from topics.
5. **Data Storage in AWS Timestream**: Storing the data in AWS Timestream for time-series analysis.

## Project Structure

The repository contains the following files:

- **generate_sensor_data.py**: A Python script that generates random values for TDS, turbidity, chlorine, and pH, and sends the data to AWS IoT and AWS Timestream.
- **aws_clients.py**: A Python script for handling the boto3 clients for various resources.
- **aws_iot_rule.py**: Create an IoT rule to route the incoming data to different AWS resources.
- **aws_iot_thing.py**: To create an AWS thing
- **aws_sqs_resources.py**: To manage the creation and deletion of queue in AWS SQS
- **main.py**: Entry point for the application

## Setup

### Prerequisites

- Python 3.x
- AWS CLI configured with the appropriate access keys.
- Boto3 and typer library installed.

To install the necessary Python libraries, run the following command:

```bash
pip install boto3
