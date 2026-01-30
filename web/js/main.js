// web/js/main.js
async function cargarSeccion(elemento, seccion) {
    // UI Update
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    elemento.classList.add('active');

    const contenedor = document.getElementById('contenedor');
    
    // Cargamos dinámicamente el módulo (esto mantiene la memoria limpia)
    try {
        switch(seccion) {
            case 'ganado':
                await initGanado(contenedor);
                break;
            case 'mixer':
                await initMixer(contenedor);
                break;
            // ... más casos
        }
    } catch (e) {
        console.error("Error cargando módulo:", e);
    }
}
