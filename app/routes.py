from flask import Blueprint, render_template, jsonify, request
from .core.attacks import attack_manager

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/documentation')
def documentation():
    return render_template('documentation.html')

# --- Attack API ---

@main.route('/api/attack/start', methods=['POST'])
def start_attack():
    data = request.json
    attack_type = data.get('type')
    iface = data.get('iface', 'eth0')
    target_ip = data.get('target_ip')
    
    success, message = attack_manager.start_attack(attack_type, iface, target_ip=target_ip)
    if success:
        return jsonify({'status': 'started', 'message': message})
    return jsonify({'status': 'error', 'message': message}), 400

@main.route('/api/attack/stop', methods=['POST'])
def stop_attack():
    data = request.json
    attack_type = data.get('type')
    
    success, message = attack_manager.stop_attack(attack_type)
    if success:
        return jsonify({'status': 'stopped', 'message': message})
    return jsonify({'status': 'error', 'message': message}), 400

@main.route('/api/attack/status', methods=['GET'])
def attack_status():
    return jsonify(attack_manager.get_status())

@main.route('/api/recon', methods=['POST'])
def run_recon():
    data = request.json
    iface = data.get('iface', 'eth0')
    result = attack_manager.run_recon(iface)
    return jsonify(result)
