# logic/dietas.jl

struct Ingrediente
    nombre::String
    porcentaje::Float64
end

# Función para validar y calcular Materia Seca (MS)
function validar_dieta(ingredientes::Vector{Ingrediente})
    total_ms = sum(i.porcentaje for i in ingredientes)
    es_valida = total_ms == 100.0
    return (total = total_ms, valida = es_valida)
end

# Función para calcular kilos reales basados en el mixer
function calcular_carga_mixer(total_kilos, ingredientes::Vector{Ingrediente})
    return [(i.nombre, (i.porcentaje / 100) * total_kilos) for i in ingredientes]
end
