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
from langchain_community.vectorstores import FAISS

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
            import time
            
            chunks = preparar_documentos(ruta_pdf)

            # Limpieza total de base de datos previa
            if os.path.exists(self.persist_directory):
                try:
                    shutil.rmtree(self.persist_directory)
                    print("Carpeta db eliminada para iniciar limpia.")
                    time.sleep(0.1)  # Breve pausa tras borrar
                except Exception as e:
                    print(f"No se pudo eliminar la base de datos anterior: {e}")

            # 2. Crear instancia nueva con FAISS
            print(f"Iniciando carga de {len(chunks)} fragmentos con FAISS...")
            try:
                self.db = FAISS.from_documents(chunks, self.embeddings)
                self.db.save_local(self.persist_directory)
                print(f"Base de datos FAISS creada exitosamente en {self.persist_directory}.")
            except Exception as e:
                print(f"Error al crear la base de datos FAISS: {e}")

        else:
            # Si no se pasa un PDF, cargamos la base de datos existente de forma segura
            if os.path.exists(self.persist_directory) and os.path.exists(os.path.join(self.persist_directory, "index.faiss")):
                try:
                    self.db = FAISS.load_local(
                        self.persist_directory, 
                        self.embeddings, 
                        allow_dangerous_deserialization=True
                    )
                    print("Base de datos FAISS cargada correctamente desde el almacenamiento persistente.")
                except Exception as e:
                    print(f"Error al cargar base de datos FAISS existente: {e}")
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