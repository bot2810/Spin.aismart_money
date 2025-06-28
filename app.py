import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import requests
from spin_logic import generate_spin_amounts, get_user_total, should_block_user

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spin_secret_default")

MAIN_BOT_TOKEN = os.environ.get("7429740172:AAEUV6A-YmDSzmL0b_0tnCCQ6SbJBEFDXbg")
VIEW_BOT_API    = os.environ.get("7547894309:AAH3zIzu5YfRDzcYBiFvzWAfW8FUTPum3g4")
ADMIN_ID        = os.environ.get("7929115529")

user_spins = {}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        telegram_id = request.form['telegram_id']
        if not telegram_id.isdigit():
            return "Invalid Telegram ID"
        session['telegram_id'] = telegram_id
        return redirect(url_for('spin'))
    return render_template('index.html')

@app.route('/spin')
def spin():
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        return redirect(url_for('login'))

    today = datetime.now().strftime('%Y-%m-%d')
    if telegram_id not in user_spins or user_spins[telegram_id]['date'] != today:
        amounts = generate_spin_amounts()
        user_spins[telegram_id] = {
            'date': today, 'spins': amounts,
            'done': False, 'current': 0
        }

    if user_spins[telegram_id]['current'] >= 15:
        return redirect(url_for('scratch'))

    return render_template('spin.html', spin_number=user_spins[telegram_id]['current'] + 1)

@app.route('/spin-result')
def spin_result():
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        return jsonify({'status': 'login', 'redirect': url_for('login')})

    if should_block_user():
        return jsonify({'status': 'blocked', 'message': 'AdBlocker or AutoClicker detected!'})

    user_data = user_spins.get(telegram_id)
    if user_data is None or user_data['current'] >= 15:
        return jsonify({'status': 'done', 'redirect': url_for('scratch')})

    earned = user_data['spins'][user_data['current']]
    user_data['current'] += 1

    try:
        requests.get(f"{VIEW_BOT_API}&chat_id={ADMIN_ID}&text=User {telegram_id} spun ₹{earned}")
    except: pass

    return jsonify({'status': 'ok', 'reward': f"₹{earned:.2f}"})

@app.route('/scratch')
def scratch():
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        return redirect(url_for('login'))

    user_data = user_spins.get(telegram_id)
    if not user_data or user_data['done']:
        return redirect(url_for('spin'))

    total = get_user_total(user_data['spins'])
    user_data['done'] = True

    try:
        requests.get(f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/sendMessage?chat_id={telegram_id}&text=/addbalance {telegram_id} {total}")
        requests.get(f"{VIEW_BOT_API}&chat_id={ADMIN_ID}&text=User {telegram_id} scratched ₹{total}")
    except: pass

    return render_template('scratch.html', total=total)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 81)))
