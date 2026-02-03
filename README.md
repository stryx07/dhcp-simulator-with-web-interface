# DHCP Attack Simulator Dashboard

A Python Flask application designed for cybersecurity education. It allows users to simulate and control various DHCP attacks via a web interface using the Scapy library.

## Features

- **Web Dashboard**: Easy-to-use Bootstrap interface.
- **Real-time Control**: Start and stop attacks independently.
- **Attack Types**:
  - DHCP Starvation
  - DHCP NAK Attack
  - DHCP Release
  - DHCP Discover Flood
  - DHCP Decline
- **Reconnaissance**: Scan for active DHCP servers.

## Prerequisites

- Linux (required for raw packet injection)
- Python 3.8+
- Root privileges (for Scapy)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd dhcp_attack_simulator
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application with `sudo` (required for network packet manipulation):
   ```bash
   sudo ./venv/bin/python run.py
   ```

2. Open your web browser and go to:
   [http://localhost:8000](http://localhost:8000)

3. Configure your Network Interface (e.g., `eth0`, `wlan0`) and Target IP in the dashboard.

## Structure

- `app/`: Main application source code.
  - `core/`: Backend logic (AttackManager, Scapy).
  - `templates/`: HTML files.
  - `static/`: CSS/JS files.
- `run.py`: Entry point.

## Disclaimer

**EDUCATIONAL USE ONLY.** This software is intended for testing and educational purposes. Using this tool on networks without permission is illegal.
