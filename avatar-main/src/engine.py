from itertools import chain
import os
import shutil
from dotenv import load_dotenv

# Modelos y embeddings (Gemini)
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)

# Vector
from langchain_chroma import Chroma

# Prompt
from langchain_core.prompts import ChatPromptTemplate

# procesamiento de documentos
from .processor import preparar_documentos

load_dotenv()


class MotorIA:
    def __init__(self):
        # Configuración del modelo Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            convert_system_message_to_human=False
        )

        # Configuración de los Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2",
            google_api_version="v1",
            task_type="retrieval_document"
        )

        # Ruta de la base de datos
        self.persist_directory = os.path.join(
            os.path.dirname(__file__), "..", "db"
        )   

        self.db = None

    def inicializar_memoria(self, ruta_pdf=None):
        # Crea la base de datos desde un PDF o la carga si ya existe.
        if ruta_pdf:
            import shutil
            import time
            import gc
            
            chunks = preparar_documentos(ruta_pdf)

            # En src/engine.py (dentro de inicializar_memoria)

            # 1. Intentar liberar la conexión de ChromaDB de la memoria
            if hasattr(self, "db") and self.db is not None:
                try:
                    # Si es el wrapper de LangChain, el cliente real está en _client
                    if hasattr(self.db, "_client") and hasattr(
                        self.db._client, "close"
                    ):
                        self.db._client.close()
                    elif hasattr(self.db, "close"):
                        self.db.close()
                except Exception as e:
                    print(f"Aviso al cerrar db: {e}")

                # Quitamos la referencia y forzamos al recolector de basura
                self.db = None

            gc.collect()
            time.sleep(0.2)  # Pausa estratégica para que Windows suelte el archivo
            
            # 2. Limpieza total de intentos fallidos
            if os.path.exists(self.persist_directory):
                try:
                    shutil.rmtree(self.persist_directory)
                    print("Carpeta db eliminada para iniciar limpia.")
                    time.sleep(0.1)  # Breve pausa tras borrar
                except PermissionError:
                    print(
                        "Windows mantiene el archivo bloqueado. Intentando borrar archivos internos..."
                    )
                    # Plan B: Si rmtree falla, vaciamos lo que se pueda antes de continuar
                    for root, dirs, files in os.walk(
                        self.persist_directory, topdown=False
                    ):
                        for name in files:
                            try:
                                os.remove(os.path.join(root, name))
                            except Exception:
                                pass

            # 2. Crear instancia nueva
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

            # 3. Inserción INDIVIDUAL con manejo de errores
            print(f"Iniciando carga de {len(chunks)} fragmentos...")
            exitos = 0
            errores = 0

            for i, chunk in enumerate(chunks):
                try:
                    # Generamos el ID único
                    origen = chunk.metadata.get("source", "documento")
                    nombre_base = os.path.basename(origen).replace(".", "_").replace(" ", "_")
                    custom_id = f"{nombre_base}_chunk_{i}"

                    # 🔥 CRUCIAL: Guardamos el ID también DENTRO de la metadata para LangChain
                    chunk.metadata["id"] = custom_id

                    # Insertamos pasando el ID explícito a Chroma
                    self.db.add_documents(documents=[chunk], ids=[custom_id])
                    exitos += 1
                    
                    if i % 5 == 0:
                        print(f"Procesados {i}/{len(chunks)} con ID: {custom_id}...")
                        time.sleep(1) 
                except Exception as e:
                    print(f"Error en chunk {i}: {e}")
                    errores += 1
                print(f"Proceso terminado. Éxitos: {exitos}, Errores: {errores}")

        else:
            # Si no se pasa un PDF, cargamos la base de datos existente de forma segura
            if os.path.exists(self.persist_directory):
                self.db = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                print("Base de datos Chroma cargada correctamente desde el almacenamiento persistente.")
            else:
                print("No hay base de datos previa y no se proporcionó PDF.")

    def pedir_respuesta(self, pregunta_usuario):
        #Ejecuta el flujo RAG para obtener una respuesta.

        if not self.db:
            self.inicializar_memoria()
            if not self.db:
                return "Error: No tengo documentos cargados en mi memoria."

        # A. Prompt
        system_prompt = """
        Eres el Asistente Virtual Oficial para los servidores judiciales del Distrito Judicial de Ibagué. Tu objetivo es resolver sus dudas administrativas y de carrera utilizando como base los fragmentos de documentos provistos.

        ────────────────────────────────────────────────────────
        📌 REGLAS DE PROCESAMIENTO Y COMPRENSIÓN (RAG)
        ────────────────────────────────────────────────────────
        1. Analiza el contenido de los fragmentos entregados dentro de las etiquetas <contexto>. Es normal que los fragmentos traten sobre temas distintos o contengan ideas fragmentadas; busca en todos ellos de manera integral.
        2. Tienes permitido parafrasear, sintetizar y conectar las ideas del contexto para dar una respuesta fluida y natural a la pregunta del usuario.
        3. LIMITACIÓN STRICTA DE DATOS DUROS: No inventes, asumas, ni agregues datos específicos que no se mencionen explícitamente en el contexto. Esto incluye:
        - Correos electrónicos o números telefónicos específicos.
        - Nombres de software o plataformas de gestión (ej. no asumas ORFEO, portales web, etc., a menos que el texto los nombre).
        - Fechas, plazos exactos o artículos de leyes que no estén escritos en los fragmentos.
        4. Si los fragmentos no contienen la información necesaria para responder a la duda, no intentes completar la respuesta con conocimiento externo. En su lugar, responde textualmente:
        "No cuento con información en los documentos disponibles para responder esa consulta."

        ────────────────────────────────────────────────────────
        🧠 ESTILO Y FORMATO DE SALIDA
        ────────────────────────────────────────────────────────
        - Responde siempre con un tono institucional, claro, respetuoso y profesional.
        - Evita incluir las etiquetas de formato del documento original (como los números de la FAQ "13. ¿Cómo...?") al final de tu redacción. Crea un texto limpio.

        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        

        # B. Retriever
        retriever = self.db.as_retriever(search_kwargs={"k": 4})

        # C. Formateo de documentos
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
        {
            "context": (lambda x: x["input"]) | retriever | format_docs,
            "input": lambda x: str(x["input"])
        }
        | prompt
        | self.llm
        )

        respuesta = chain.invoke({"input": pregunta_usuario})

        return respuesta.content 