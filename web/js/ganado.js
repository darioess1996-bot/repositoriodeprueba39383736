// web/js/ganado.js
async function initGanado(container) {
    container.innerHTML = `
        <div class="header-title"><span>VIALAC - GESTIÓN DE HATO</span></div>
        <div class="card">
            <div class="manga-input">
                <input type="number" id="input-caravana" placeholder="N° CARAVANA" autofocus>
                <button onclick="buscarAnimal()">BUSCAR</button>
            </div>
            <div id="ficha-animal" class="grid-widgets">
                </div>
        </div>
    `;
    // Foco automático para usar con lectores de caravanas o teclado numérico rápido
    document.getElementById('input-caravana').focus();
}

async function buscarAnimal() {
    const caravana = document.getElementById('input-caravana').value;
    const datos = await pywebview.api.obtener_ficha_animal(caravana);
    renderizarFicha(datos);
}
