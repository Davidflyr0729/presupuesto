// auth.js - Asegurar guardado correcto del usuario
const API_URL = '/api';

async function login() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
        alert('❌ Por favor completa todos los campos');
        return;
    }

    // Limpiar sesión anterior
    localStorage.removeItem('user_info');

    // Mostrar loading
    const btnLogin = document.querySelector('.btn-login');
    const originalText = btnLogin.textContent;
    btnLogin.textContent = '⏳ Iniciando sesión...';
    btnLogin.disabled = true;

    try {
        console.log('🔐 Login para:', email);
        
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ email, password })
        });

        console.log('📨 Status:', response.status);

        const result = await response.json();
        console.log('📊 Resultado completo:', result);

        btnLogin.textContent = originalText;
        btnLogin.disabled = false;

        if (result.success && result.usuario) {
            console.log('✅ Login exitoso - Usuario:', result.usuario);
            
            // Guardar usuario COMPLETO como viene del servidor
            localStorage.setItem('user_info', JSON.stringify(result.usuario));
            console.log('💾 Usuario guardado en localStorage');
            
            // Pequeño delay antes de redireccionar
            setTimeout(() => {
                console.log('🔄 Redirigiendo a dashboard...');
                window.location.href = 'dashboard.html';
            }, 200);
            
        } else {
            console.error('❌ Error del servidor:', result.error);
            alert('❌ ' + (result.error || 'Error desconocido'));
        }

    } catch (error) {
        console.error('💥 Error de conexión:', error);
        btnLogin.textContent = originalText;
        btnLogin.disabled = false;
        alert('❌ Error de conexión: ' + error.message);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Login page cargada');
    
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            login();
        });
    }
});

window.login = login;