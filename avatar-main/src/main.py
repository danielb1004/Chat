from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .engine import MotorIA

import os

# 1. Configuración de la App
app = FastAPI(
    title="API Asistente IA",
    description="Backend para consulta de documentos usando RAG con Gemini 2.5 Flash",
    version="1.0.0"
)

# 2. Permisos CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # URL front
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Instancia del motor
motor = MotorIA()

# Modelo de datos
class Consulta(BaseModel):
    pregunta: str

@app.get("/")
def read_root():
    return {"status": "Online", "modelo": "Gemini 2.5 Flash"}

@app.post("/assistant/chat")
async def chat(consulta: Consulta):
    """Endpoint para que el frontend envíe preguntas"""
    if not consulta.pregunta:
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
    
    try:
        respuesta = motor.pedir_respuesta(consulta.pregunta)
        return {"respuesta": respuesta}
    except Exception as e:
        print(f"Error en el motor: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar la IA")

@app.get("/settings")
async def configurar_base_datos():
    #Ruta para cargar el PDF inicial manualmente
    docs_path = os.path.join(os.path.dirname(__file__), "..", "docs")
    archivos = [f for f in os.listdir(docs_path) if f.endswith('.pdf')]
    
    if not archivos:
        return {"error": "No se encontró ningún PDF en la carpeta docs/"}
    
    ruta_completa = os.path.join(docs_path, archivos[0])
    motor.inicializar_memoria(ruta_completa)
    
    return {"mensaje": f"Base de datos cargada exitosamente con {archivos[0]}"}

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Sirve la interfaz gráfica de administración"""
    admin_html_path = os.path.join(os.path.dirname(__file__), "admin.html")
    try:
        with open(admin_html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail="No se pudo cargar la interfaz de administración")

@app.post("/admin/upload")
async def upload_document(file: UploadFile = File(...), password: str = Form(...)):
    """Recibe un PDF y contraseña, valida y actualiza la base de conocimiento"""
    # 1. Validar contraseña
    admin_pwd = os.getenv("ADMIN_PASSWORD", "admin123")
    if password != admin_pwd:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
    
    docs_path = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(docs_path, exist_ok=True)
    
    # 2. Eliminar PDFs antiguos para mantener solo el actual
    for f in os.listdir(docs_path):
        if f.endswith('.pdf'):
            try:
                os.remove(os.path.join(docs_path, f))
            except Exception as e:
                print(f"No se pudo eliminar {f}: {e}")
            
    # 3. Guardar nuevo archivo
    file_path = os.path.join(docs_path, file.filename)
    try:
        import shutil
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {e}")
        
    # 4. Actualizar base de datos FAISS
    try:
        motor.inicializar_memoria(file_path)
        return {"mensaje": f"Base de datos actualizada con éxito: {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar en FAISS: {e}")

@app.on_event("startup")
async def startup_event():
    db_path = os.path.join(os.path.dirname(__file__), "..", "db")
    # Solo autoconfiguramos si la carpeta db no existe o está vacía
    if not os.path.exists(db_path) or len(os.listdir(db_path)) == 0:
        print("Iniciando autoconfiguración de base de datos (Primera vez)...")
        resultado = await configurar_base_datos()
        print(f"Resultado de autoconfiguración: {resultado}")
    else:
        print("La base de datos ya existe. Saltando autoconfiguración para ahorrar tiempo y recursos.")
        # Opcional: motor.inicializar_memoria() sin ruta_pdf para cargar la BD existente
        motor.inicializar_memoria()

@app.get("/modelo")
def obtener_registros():
    if not motor.db:
        return {
            "coleccion": "faiss",
            "cantidad_registros": 0,
            "registros": []
        }

    registros = []
    
    # En FAISS, los documentos se encuentran en el docstore
    for doc_id, doc in motor.db.docstore._dict.items():
        registros.append({
            "id": doc_id,
            "documento": doc.page_content,
            "metadata": doc.metadata
        })

    return {
        "coleccion": "faiss",
        "cantidad_registros": len(registros),
        "registros": registros
    }