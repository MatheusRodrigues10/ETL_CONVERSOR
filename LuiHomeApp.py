import subprocess
import webbrowser
import os
import sys
import tkinter as tk
from tkinter import messagebox
import http.server
import socketserver
import threading
import socket

SERVER_PROCESS = None
HTTP_SERVER = None

# Corrige o caminho base para funcionar como executável
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_PATH = os.path.join(BASE_DIR, "..", "JSON")
DIST_PATH = os.path.join(PROJECT_PATH, "dist")
CONFIG_PATH = os.path.join(BASE_DIR, "..", "MOTOR", "configs")
PLANILHAS_PATH = os.path.join(BASE_DIR, "..", "MOTOR", "planilhas")

PROJECT_PATH = os.path.abspath(PROJECT_PATH)
DIST_PATH = os.path.abspath(DIST_PATH)
CONFIG_PATH = os.path.abspath(CONFIG_PATH)
PLANILHAS_PATH = os.path.abspath(PLANILHAS_PATH)

def find_available_port(start_port=8000):
    """Encontra uma porta disponível"""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return None

def build_project():
    """Faz o build do projeto Vite"""
    try:
        btn_build.config(state="disabled", text="Buildando...")
        app.update()
        
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=PROJECT_PATH,
            capture_output=True,
            text=True,
            shell=True,
            timeout=120
        )
        
        btn_build.config(state="normal", text="Gerar novo build")
        
        if result.returncode == 0:
            messagebox.showinfo("Sucesso", "Build criado com sucesso!")
            return True
        else:
            messagebox.showerror("Erro", f"Erro no build:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        btn_build.config(state="normal", text="Gerar novo build")
        messagebox.showerror("Erro", "Build demorou muito tempo (timeout)")
        return False
    except Exception as e:
        btn_build.config(state="normal", text="Gerar novo build")
        messagebox.showerror("Erro", f"Erro ao executar build:\n{str(e)}")
        return False

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler customizado para evitar logs no console"""
    def log_message(self, format, *args):
        pass  # Silencia os logs

def serve_static_files(port):
    """Serve arquivos estáticos da pasta dist"""
    global HTTP_SERVER
    
    try:
        original_dir = os.getcwd()
        os.chdir(DIST_PATH)
        
        HTTP_SERVER = socketserver.TCPServer(("", port), MyHTTPRequestHandler)
        HTTP_SERVER.serve_forever()
    except Exception as e:
        print(f"Erro no servidor: {e}")
        messagebox.showerror("Erro no Servidor", f"Erro ao iniciar servidor:\n{str(e)}")
    finally:
        os.chdir(original_dir)

def start_server_thread():
    """Inicia o servidor em thread separada"""
    global HTTP_SERVER
    
    try:
        # Verifica se existe build
        if not os.path.exists(DIST_PATH):
            messagebox.showerror("Erro", f"Pasta dist não encontrada em:\n{DIST_PATH}")
            btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal")
            return
        
        if not os.listdir(DIST_PATH):
            response = messagebox.askyesno(
                "Build vazio",
                "A pasta dist está vazia.\nDeseja criar o build agora?"
            )
            if response:
                if not build_project():
                    btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal")
                    return
            else:
                btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal")
                return
        
        # Encontra porta disponível
        port = find_available_port(8000)
        if not port:
            messagebox.showerror("Erro", "Nenhuma porta disponível.")
            btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal")
            return
        
        # Inicia servidor em thread separada
        server_thread = threading.Thread(
            target=serve_static_files,
            args=(port,),
            daemon=True
        )
        server_thread.start()
        
        # Aguarda um pouco para garantir que o servidor iniciou
        import time
        time.sleep(1)
        
        # Verifica se o servidor está rodando
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', port))
            
            # Servidor está rodando, abre navegador
            url = f"http://localhost:{port}"
            webbrowser.open(url)
            
            btn_toggle.config(
                text=f"Desligar servidor (:{port})",
                bg="#ffaaaa",
                state="normal"
            )
        except:
            messagebox.showerror("Erro", "Servidor não iniciou corretamente")
            btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal")
            
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar servidor:\n{str(e)}")
        btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal")

def toggle_server():
    global HTTP_SERVER
    
    if HTTP_SERVER is None:
        btn_toggle.config(text="Iniciando servidor...", state="disabled", bg="#ffffaa")
        app.update()
        
        # Inicia em thread separada para não travar a UI
        threading.Thread(target=start_server_thread, daemon=True).start()
    else:
        # Para o servidor
        try:
            HTTP_SERVER.shutdown()
            HTTP_SERVER.server_close()
        except:
            pass
        HTTP_SERVER = None
        btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal")

def open_configs():
    if os.path.exists(CONFIG_PATH):
        os.startfile(CONFIG_PATH)
    else:
        messagebox.showerror("Erro", f"Pasta configs não encontrada em:\n{CONFIG_PATH}")

def open_planilhas():
    if os.path.exists(PLANILHAS_PATH):
        os.startfile(PLANILHAS_PATH)
    else:
        messagebox.showerror("Erro", f"Pasta planilhas não encontrada em:\n{PLANILHAS_PATH}")

app = tk.Tk()
app.title("Lui Home")
app.geometry("450x300")
app.configure(bg="#e7e7e7")

frame = tk.Frame(app, bg="#ffffff", padx=25, pady=25)
frame.pack(expand=True)

title = tk.Label(frame, text="Servidor Local", font=("Segoe UI", 14), bg="#ffffff")
title.pack(pady=(0, 10))

btn_toggle = tk.Button(
    frame,
    text="Ligar servidor",
    width=22,
    height=2,
    command=toggle_server,
    bg="#c8ffc8",
    relief="flat",
    font=("Segoe UI", 10)
)
btn_toggle.pack(pady=10)

btn_build = tk.Button(
    frame,
    text="Gerar novo build",
    width=22,
    command=build_project,
    bg="#e0e0e0",
    relief="flat",
    font=("Segoe UI", 9)
)
btn_build.pack(pady=5)

# Label de status
status_label = tk.Label(frame, text="", font=("Segoe UI", 8), bg="#ffffff", fg="#666")
status_label.pack(pady=5)

# Atualiza status no carregamento
if os.path.exists(DIST_PATH) and os.listdir(DIST_PATH):
    status_label.config(text="✓ Build encontrado", fg="green")
else:
    status_label.config(text="⚠ Build não encontrado", fg="orange")

bottom_frame = tk.Frame(app, bg="#e7e7e7")
bottom_frame.pack(side="bottom", anchor="se", padx=15, pady=15)

btn_configs = tk.Button(
    bottom_frame,
    text="Abrir configs",
    width=15,
    command=open_configs,
    bg="#dcdcdc",
    relief="flat",
    font=("Segoe UI", 9)
)
btn_configs.grid(row=0, column=0, padx=5)

btn_planilhas = tk.Button(
    bottom_frame,
    text="Abrir planilhas",
    width=15,
    command=open_planilhas,
    bg="#dcdcdc",
    relief="flat",
    font=("Segoe UI", 9)
)
btn_planilhas.grid(row=0, column=1, padx=5)

def on_closing():
    global HTTP_SERVER
    if HTTP_SERVER:
        try:
            HTTP_SERVER.shutdown()
            HTTP_SERVER.server_close()
        except:
            pass
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()