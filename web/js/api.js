// web/js/api.js - El puente hacia el orquestador Python
const VialacAPI = {
    // Comando para obtener datos del animal
    async getAnimal(caravana) {
        try {
            return await pywebview.api.procesar_comando('CONSULTAR_ANIMAL', { caravana });
        } catch (e) {
            console.error("Error en orquestador:", e);
            return { error: "Servidor no responde" };
        }
    },

    // Comando para registrar eventos de manga
    async registrarEvento(tipo, datos) {
        return await pywebview.api.procesar_comando('REGISTRAR_EVENTO', { tipo, ...datos });
    }
};
