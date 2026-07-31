from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from motor_usgs import obtener_sismos_caribe, calcular_probabilidades_bayes_poisson

# Inicializamos la aplicación
app = FastAPI(title="API de SismoProb RD")

# 1. Montamos la carpeta de archivos estáticos (para iconos, PWA y assets)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Ruta principal que sirve tu mapa (index.html)
@app.get("/", response_class=HTMLResponse)
def ruta_principal():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 3. Ruta de la API de sismos con el modelo estadístico Bayes-Poisson
@app.get("/api/sismos")
def api_sismos():
    sismos = obtener_sismos_caribe(magnitud_minima=3.0)
    estadisticas = calcular_probabilidades_bayes_poisson(sismos)
    
    return {
        "estado": "exito",
        "total_eventos": len(sismos),
        "modelo_matematico": estadisticas,
        "datos": sismos
    }
