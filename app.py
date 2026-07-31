from fastapi import FastAPI
from motor_usgs import obtener_sismos_caribe

# Inicializamos la aplicación
app = FastAPI(title="API de SismoProb RD")

@app.get("/")
def ruta_principal():
    return {"mensaje": "El motor de SismoProb RD está en línea 🟢. Visita http://127.0.0.1:8000/api/sismos"}

@app.get("/api/sismos")
def api_sismos():
    # Aquí nuestro servidor web llama a tu motor de datos
    datos = obtener_sismos_caribe(magnitud_minima=3.0)
    return {
        "estado": "exito",
        "total_eventos": len(datos),
        "datos": datos
    }
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from motor_usgs import obtener_sismos_caribe

app = FastAPI(title="API de SismoProb RD")

@app.get("/", response_class=HTMLResponse)
def ruta_principal():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/sismos")
def api_sismos():
    datos = obtener_sismos_caribe(magnitud_minima=3.0)
    return {
        "estado": "exito",
        "total_eventos": len(datos),
        "datos": datos
    }

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from motor_usgs import obtener_sismos_caribe, calcular_probabilidades_bayes_poisson

app = FastAPI(title="API de SismoProb RD")

@app.get("/", response_class=HTMLResponse)
def ruta_principal():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/sismos")
def api_sismos():
    # 1. Obtenemos los sismos filtrados
    sismos = obtener_sismos_caribe(magnitud_minima=3.0)
    
    # 2. Aplicamos el modelo estadístico Bayes-Poisson
    estadisticas = calcular_probabilidades_bayes_poisson(sismos)
    
    return {
        "estado": "exito",
        "total_eventos": len(sismos),
        "modelo_matematico": estadisticas,
        "datos": sismos
    }
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Monta la carpeta 'static' para que la app pueda leer los iconos y archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# ... (el resto de tus rutas o código de la app)
