# DHCP Attack Simulator Dashboard v2.0

> **EDUCATIONAL USE ONLY.** This software is intended for testing and educational purposes. Using this tool on networks without permission is illegal.

A Python Flask application designed for cybersecurity education. It allows users to simulate and control various DHCP attacks via a premium, real-time web interface using the Scapy library.

## ✨ New Features v2.0

-   **Premium Dark UI**: Glassmorphism design with real-time animations.
-   **Live Metrics**: Real-time chart showing attack intensity (packets/second).
-   **Operation Logs**: Live terminal-style log window of all attack events.
-   **Rogue DHCP Server**: New module to simulate a MITM Rogue Server.

## 🛡 Attack Modules

1.  **DHCP Starvation**: Exhausts the DHCP server's IP pool by flooding requests from random MAC addresses.
2.  **DHCP Discover Flood**: A DoS attack that overwhelms the server with high-frequency DISCOVER packets.
3.  **DHCP Release**: Spoofs a victim's MAC address to send a RELEASE packet, disconnecting them from the network.
4.  **DHCP Decline**: Marks arbitrary IPs as "in use" by sending false DECLINE messages.
5.  **Rogue Server**: Listens for DISCOVER packets and replies with a malicious OFFER (fake Gateway/DNS).

## 🚀 Installation & Usage

### Prerequisites
-   Linux (Root privileges required for raw packet injection)
-   Python 3.8+

### Setup
1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd dhcp_attack_simulator
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run the Application**:
    ```bash
    sudo ./venv/bin/python run.py
    ```
    *Note: `sudo` is required for Scapy to send/receive packets.*

4.  **Access Dashboard**:
    Open [http://localhost:8000](http://localhost:8000)

## 📚 Educational Scenarios

### Scenario 1: Denial of Service (DoS)
**Goal**: Prevent new users from joining the network.
**Method**: Start the **Starvation** attack. Observe the server's logs filling up and the IP pool depleting. New clients will fail to get an IP.

### Scenario 2: Man-in-the-Middle (MITM) prep
**Goal**: Direct client traffic through your machine.
**Method**:
1.  Run **DHCP Starvation** to exhaust legitimate IPs.
2.  Start the **Rogue Server**.
3.  When a legitimate client retries, your Rogue Server will offer an IP with **YOUR** IP as the Gateway.

## ⚠️ Disclaimer
This tool exploits standard DHCP protocol weaknesses (lack of authentication). It should only be used in isolated lab environments.
