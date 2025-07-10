# license_server.py
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Base de datos simple (en producción usa una DB real)
licenses_db = {
    "LIC123": {
        "active": True,
        "expiry": "2024-12-31",
        "hw_ids": [],
        "max_devices": 1
    }
}

@app.route('/verify_license', methods=['POST'])
def verify_license():
    data = request.get_json()
    
    if not data or 'license_key' not in data:
        return jsonify({"valid": False, "reason": "invalid_request"})
    
    license_key = data['license_key']
    hw_id = data.get('hw_id', '')
    
    if license_key not in licenses_db:
        return jsonify({"valid": False, "reason": "invalid_key"})
    
    license_data = licenses_db[license_key]
    
    # Verificar licencia activa
    if not license_data['active']:
        return jsonify({"valid": False, "reason": "license_inactive"})
    
    # Verificar fecha de expiración
    if datetime.now() > datetime.strptime(license_data['expiry'], "%Y-%m-%d"):
        return jsonify({"valid": False, "reason": "license_expired"})
    
    # Verificar dispositivo
    if license_data['hw_ids']:
        if hw_id not in license_data['hw_ids']:
            if len(license_data['hw_ids']) >= license_data['max_devices']:
                return jsonify({"valid": False, "reason": "device_limit"})
            license_data['hw_ids'].append(hw_id)
    
    return jsonify({
        "valid": True,
        "expiry": license_data['expiry'],
        "devices": len(license_data['hw_ids'])
    })

if __name__ == '__main__':
    app.run()