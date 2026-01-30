# logic/analytics.jl

# Estructura para representar los datos de una vaca o el tanque
struct RegistroProduccion
    litros::Float64
    grasa::Float64
    proteina::Float64
end

# Función para analizar la calidad (lo que hacía tu TS)
function analizar_calidad(datos::Vector{RegistroProduccion})
    total_lts = sum(d.litros for d in datos)
    prom_grasa = sum(d.grasa for d in datos) / length(datos)
    prom_prot = sum(d.proteina for d in datos) / length(datos)
    
    return (
        litros_total = round(total_lts, digits=2),
        grasa_avg = round(prom_grasa, digits=2),
        proteina_avg = round(prom_prot, digits=2)
    )
end
