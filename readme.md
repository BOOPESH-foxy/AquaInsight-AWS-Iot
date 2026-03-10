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
```
    aquaInsight/
    ├── main.py                         # Typer-based CLI entry point
    ├── aws_clients.py                  # Centralized boto3 clients
    ├── aws_iot/
    │   ├── aws_iot_iam_role.py         # Creates IAM role for IoT → SQS communication
    │   └── aws_iot_resources.py        # Handles IoT Thing & rule creation
    ├── aws_sqs/
    │   └── aws_sqs_resources.py        # Creates and manages SQS queues
    ├── sensor_data_operations/
    │   ├── generate_sensor_data.py     # Generates random sensor readings
    │   ├── publish_sensor_data.py      # Publishes readings to IoT Core topics
    │   └── tank_metadata.py            # Holds metadata (tank ID, district, village)
    ├── sequence.py                     # Orchestrates setup across IoT and SQS
    └── readme.md
```

## Setup

### Prerequisites

- Python 3.x
- AWS CLI configured with the appropriate access keys.
- Boto3 and typer library installed.

To install the necessary Python libraries, run the following command:

```bash
pip install boto3 python-dotenv typer
```

### Configuration Management

The application uses AWS Systems Manager (SSM) Parameter Store for production configuration management with `.env` file fallback for local development.

#### Initial Setup (One-time)
```bash
# 1. Configure your .env file with required values
cp .env.example .env
# Edit .env with your AWS account details

# 2. Populate SSM Parameter Store
python main.py populate_ssm
```

#### Configuration Sources
- **Production**: AWS SSM Parameter Store (`/aquainsight/*` parameters)
- **Development**: Local `.env` file (automatic fallback)


