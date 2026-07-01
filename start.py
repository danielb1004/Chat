import os
import sys
import subprocess
import threading
import time

processes = []

def run_process(prefix, command, cwd):
    """Ejecuta un proceso y captura su salida línea por línea"""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(process)
        
        for line in iter(process.stdout.readline, ''):
            print(f"[{prefix}] {line}", end='')
            
        process.stdout.close()
        process.wait()
    except Exception as e:
        print(f"[{prefix}] Error al ejecutar el proceso: {e}")

def start_backend():
    print("[BACKEND] Configurando el entorno del backend...")
    backend_dir = os.path.join(os.getcwd(), 'avatar-main')
    venv_dir = os.path.join(backend_dir, 'venv')
    
    # 1. Crear entorno virtual si no existe
    if not os.path.exists(venv_dir):
        print("[BACKEND] Creando entorno virtual...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], cwd=backend_dir)
    
    # 2. Definir ejecutable de Python dependiendo del SO (Windows vs Mac/Linux)
    if os.name == 'nt':
        python_exe = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        python_exe = os.path.join(venv_dir, 'bin', 'python')
        
    # 3. Instalar dependencias
    print("[BACKEND] Instalando dependencias de Python...")
    subprocess.run([python_exe, '-m', 'pip', 'install', '-r', 'requirements.txt'], cwd=backend_dir)
    
    # 4. Iniciar el servidor
    print("[BACKEND] Levantando servidor FastAPI...")
    run_process("BACKEND", [python_exe, '-m', 'uvicorn', 'src.main:app', '--host', '0.0.0.0', '--reload'], cwd=backend_dir)

def start_frontend():
    print("[FRONTEND] Configurando el entorno del frontend...")
    frontend_dir = os.getcwd()
    
    # 1. Definir comando npm dependiendo del SO
    npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
    
    # 2. Instalar node_modules si no existe
    if not os.path.exists(os.path.join(frontend_dir, 'node_modules')):
        print("[FRONTEND] Instalando dependencias de Node...")
        subprocess.run([npm_cmd, 'install'], cwd=frontend_dir)
    
    # 3. Iniciar servidor Vite
    print("[FRONTEND] Levantando servidor Vite...")
    run_process("FRONTEND", [npm_cmd, 'run', 'dev'], cwd=frontend_dir)

if __name__ == '__main__':
    print("Iniciando servicios. Presiona Ctrl+C para detener ambos.")
    
    # Iniciar procesos en hilos separados
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    
    backend_thread.start()
    frontend_thread.start()
    
    try:
        # Mantener el script vivo mientras corren los hilos
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SISTEMA] Deteniendo los servidores...")
        for p in processes:
            p.terminate()
        print("[SISTEMA] Hasta luego.")
        sys.exit(0)
