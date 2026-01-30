# logic/alimentacion.jl

struct CargaMixer
    fecha::String
    rodeo::String
    ingrediente::String
    orden_mezcla::Int
    kg_teorico::Float64
    kg_real::Float64
    desvio::Float64
end

# Traduciendo tu función 'analizarCalidadRacion' de alimentacion_logic.ts
function analizar_calidad_mixer(datos::Vector{CargaMixer})
    alertas = []
    
    # 1. Validar Orden (Alfalfa siempre 1)
    mal_orden = filter(d -> d.ingrediente == "Heno de Alfalfa" && d.orden_mezcla != 1, datos)
    if !isempty(mal_orden)
        push!(alertas, "CRÍTICO: Alfalfa fuera de orden en $(length(mal_orden)) cargas.")
    end

    # 2. Validar Desvíos > 5%
    desvios_grandes = filter(d -> abs(d.desvio) > (d.kg_teorico * 0.05), datos)
    if !isempty(desvios_grandes)
        push!(alertas, "ADVERTENCIA: $(length(desvios_grandes)) cargas con error > 5%.")
    end

    return alertas
end
