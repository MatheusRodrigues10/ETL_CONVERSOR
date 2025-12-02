import subprocess
import webbrowser
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import http.server
import socketserver
import threading
import socket
import shutil

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
MOTOR_PATH = os.path.join(BASE_DIR, "..", "MOTOR")
TRADUTOR_PATH = os.path.join(BASE_DIR, "..", "TRADUTOR")

PROJECT_PATH = os.path.abspath(PROJECT_PATH)
DIST_PATH = os.path.abspath(DIST_PATH)
CONFIG_PATH = os.path.abspath(CONFIG_PATH)
PLANILHAS_PATH = os.path.abspath(PLANILHAS_PATH)
MOTOR_PATH = os.path.abspath(MOTOR_PATH)
TRADUTOR_PATH = os.path.abspath(TRADUTOR_PATH)

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

def get_python_executable():
    """Retorna o caminho do Python correto"""
    python_commands = ['python', 'python3', 'py']
    
    for cmd in python_commands:
        try:
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return cmd
        except:
            continue
    
    return 'python'

def restart_app():
    """Reinicia o aplicativo"""
    global HTTP_SERVER
    
    stop_server()
    
    if getattr(sys, 'frozen', False):
        os.execl(sys.executable, sys.executable)
    else:
        os.execl(sys.executable, sys.executable, *sys.argv)

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
            response = messagebox.askyesno(
                "Build Concluído", 
                "Build criado com sucesso!\n\nDeseja reiniciar o aplicativo para aplicar as mudanças?"
            )
            if response:
                restart_app()
            else:
                status_label.config(text="✓ Build atualizado", fg="green")
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
        pass

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
    finally:
        try:
            os.chdir(original_dir)
        except:
            pass

def start_server_thread():
    """Inicia o servidor em thread separada"""
    global HTTP_SERVER
    
    try:
        if not os.path.exists(DIST_PATH):
            app.after(0, lambda: messagebox.showerror("Erro", f"Pasta dist não encontrada em:\n{DIST_PATH}"))
            app.after(0, lambda: btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal"))
            return
        
        if not os.listdir(DIST_PATH):
            response = messagebox.askyesno(
                "Build vazio",
                "A pasta dist está vazia.\nDeseja criar o build agora?"
            )
            if response:
                if not build_project():
                    app.after(0, lambda: btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal"))
                    return
            else:
                app.after(0, lambda: btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal"))
                return
        
        port = find_available_port(8000)
        if not port:
            app.after(0, lambda: messagebox.showerror("Erro", "Nenhuma porta disponível."))
            app.after(0, lambda: btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal"))
            return
        
        server_thread = threading.Thread(
            target=serve_static_files,
            args=(port,),
            daemon=True
        )
        server_thread.start()
        
        import time
        time.sleep(1)
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', port))
            
            url = f"http://localhost:{port}"
            webbrowser.open(url)
            
            app.after(0, lambda: btn_toggle.config(
                text=f"Desligar servidor (:{port})",
                bg="#ffaaaa",
                state="normal"
            ))
            app.after(0, lambda: status_label.config(text=f"✓ Servidor rodando na porta {port}", fg="green"))
        except:
            app.after(0, lambda: messagebox.showerror("Erro", "Servidor não iniciou corretamente"))
            app.after(0, lambda: btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal"))
            
    except Exception as e:
        app.after(0, lambda: messagebox.showerror("Erro", f"Erro ao iniciar servidor:\n{str(e)}"))
        app.after(0, lambda: btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal"))

def stop_server():
    """Para o servidor HTTP"""
    global HTTP_SERVER
    
    if HTTP_SERVER is not None:
        try:
            HTTP_SERVER.shutdown()
        except:
            pass
        
        try:
            HTTP_SERVER.server_close()
        except:
            pass
        
        HTTP_SERVER = None

def toggle_server():
    global HTTP_SERVER
    
    if HTTP_SERVER is None:
        # Ligar servidor
        btn_toggle.config(text="Iniciando servidor...", state="disabled", bg="#ffffaa")
        app.update()
        
        threading.Thread(target=start_server_thread, daemon=True).start()
    else:
        # Desligar servidor
        btn_toggle.config(state="disabled", text="Desligando...")
        app.update()
        
        def desligar_thread():
            stop_server()
            app.after(0, lambda: btn_toggle.config(text="Ligar servidor", bg="#c8ffc8", state="normal"))
            app.after(0, lambda: status_label.config(text="✓ Servidor desligado", fg="green"))
        
        threading.Thread(target=desligar_thread, daemon=True).start()

def run_script(script_path, cwd, script_name):
    """Executa um script Python e retorna o resultado"""
    try:
        python_cmd = get_python_executable()
        
        result = subprocess.run(
            [python_cmd, script_path],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
            shell=False
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, f"{script_name} demorou muito tempo (timeout)"
    except Exception as e:
        return False, str(e)

def count_files(directory, extension=""):
    """Conta arquivos em um diretório"""
    try:
        if not os.path.exists(directory):
            return 0
        files = [f for f in os.listdir(directory) if f.endswith(extension)]
        return len(files)
    except:
        return 0

def iniciar_processo():
    """Inicia o processo ETL completo"""
    
    btn_processo.config(state="disabled", text="Processando...")
    app.update()
    
    try:
        # ETAPA 1: Conversor ETL (Excel → TXT)
        status_label.config(text="⏳ Etapa 1/5: Conversor ETL (Excel → TXT)...", fg="blue")
        app.update()
        
        conversor_path = os.path.join(MOTOR_PATH, "conversor_etl.py")
        success, output = run_script(conversor_path, MOTOR_PATH, "conversor_etl")
        
        if not success:
            messagebox.showerror("Erro no Conversor", f"Erro ao executar conversor_etl.py:\n{output}")
            btn_processo.config(state="normal", text="Iniciar Processo")
            status_label.config(text="✗ Erro no conversor", fg="red")
            return
        
        txt_bruto_path = os.path.join(MOTOR_PATH, "txt_bruto")
        txt_count = count_files(txt_bruto_path, ".txt")
        
        # ETAPA 2: Gerador JSON (TXT → JSON)
        status_label.config(text="⏳ Etapa 2/5: Gerador JSON (TXT → JSON)...", fg="blue")
        app.update()
        
        gerador_path = os.path.join(MOTOR_PATH, "geradorJSON.py")
        success, output = run_script(gerador_path, MOTOR_PATH, "geradorJSON")
        
        if not success:
            messagebox.showerror("Erro no Gerador JSON", f"Erro ao executar geradorJSON.py:\n{output}")
            btn_processo.config(state="normal", text="Iniciar Processo")
            status_label.config(text="✗ Erro no gerador JSON", fg="red")
            return
        
        json_final_path = os.path.join(MOTOR_PATH, "json_final")
        json_count = count_files(json_final_path, ".json")
        
        # ETAPA 3: Mesclador JSON
        status_label.config(text="⏳ Etapa 3/5: Mesclador JSON...", fg="blue")
        app.update()
        
        mesclador_path = os.path.join(MOTOR_PATH, "mescladorJSON.py")
        success, output = run_script(mesclador_path, MOTOR_PATH, "mescladorJSON")
        
        if not success:
            messagebox.showerror("Erro no Mesclador", f"Erro ao executar mescladorJSON.py:\n{output}")
            btn_processo.config(state="normal", text="Iniciar Processo")
            status_label.config(text="✗ Erro no mesclador", fg="red")
            return
        
        jsons_mesclados_path = os.path.join(MOTOR_PATH, "jsons_mesclados")
        mesclados_count = count_files(jsons_mesclados_path, ".json")
        
        # PERGUNTA: Usar separadorVariacoes?
        status_label.config(text="⏸️ Aguardando escolha do usuário...", fg="orange")
        app.update()
        
        usar_regex = messagebox.askyesno(
            "Separador de Variações",
            "Deseja usar o separadorVariacoes.py?\n\n"
            "Sim = Usa json_com_regex\n"
            "Não = Usa jsons_mesclados"
        )
        
        source_folder = ""
        etapa_atual = 4
        
        if usar_regex:
            # ETAPA 4: Separador de Variações
            status_label.config(text="⏳ Etapa 4/5: Separador de Variações...", fg="blue")
            app.update()
            
            separador_path = os.path.join(MOTOR_PATH, "separadorVariacoes.py")
            success, output = run_script(separador_path, MOTOR_PATH, "separadorVariacoes")
            
            if not success:
                messagebox.showerror("Erro no Separador", f"Erro ao executar separadorVariacoes.py:\n{output}")
                btn_processo.config(state="normal", text="Iniciar Processo")
                status_label.config(text="✗ Erro no separador", fg="red")
                return
            
            source_folder = os.path.join(MOTOR_PATH, "json_com_regex")
            regex_count = count_files(source_folder, ".json")
        else:
            source_folder = jsons_mesclados_path
        
        # Copia JSONs para pasta do TRADUTOR
        status_label.config(text=f"⏳ Etapa {etapa_atual}/5: Copiando JSONs...", fg="blue")
        app.update()
        
        tradutor_jsons_path = os.path.join(TRADUTOR_PATH, "jsons")
        
        os.makedirs(tradutor_jsons_path, exist_ok=True)
        
        for file in os.listdir(tradutor_jsons_path):
            file_path = os.path.join(tradutor_jsons_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Erro ao deletar {file_path}: {e}")
        
        copied_count = 0
        for file in os.listdir(source_folder):
            if file.endswith(".json"):
                src = os.path.join(source_folder, file)
                dst = os.path.join(tradutor_jsons_path, file)
                shutil.copy2(src, dst)
                copied_count += 1
        
        # ETAPA FINAL: Tradutor
        status_label.config(text="⏳ Etapa 5/5: Tradutor Final (JSON → Excel)...", fg="blue")
        app.update()
        
        tradutor_script_path = os.path.join(TRADUTOR_PATH, "tradutor_final.py")
        success, output = run_script(tradutor_script_path, TRADUTOR_PATH, "tradutor_final")
        
        if not success:
            messagebox.showerror("Erro no Tradutor", f"Erro ao executar tradutor_final.py:\n{output}")
            btn_processo.config(state="normal", text="Iniciar Processo")
            status_label.config(text="✗ Erro no tradutor", fg="red")
            return
        
        saidas_path = os.path.join(TRADUTOR_PATH, "saidas")
        excel_count = count_files(saidas_path, ".xlsx")
        
        # SUCESSO!
        status_label.config(text="✓ Processo concluído com sucesso!", fg="green")
        
        response = messagebox.askyesno(
            "Processo Concluído! 🎉",
            f"Todo o processo ETL foi executado com sucesso!\n\n"
            f"📄 {txt_count} arquivos TXT\n"
            f"📋 {json_count} JSONs individuais\n"
            f"🔗 {mesclados_count} JSONs mesclados\n"
            f"📊 {copied_count} JSONs copiados\n"
            f"📁 {excel_count} planilhas Excel geradas\n\n"
            f"Deseja abrir a pasta de saída?"
        )
        
        if response:
            os.startfile(saidas_path)
        
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Erro durante o processo:\n{str(e)}")
        status_label.config(text="✗ Erro no processo", fg="red")
    finally:
        btn_processo.config(state="normal", text="Iniciar Processo")

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

# Interface
app = tk.Tk()
app.title("Lui Home - ETL Manager")
app.geometry("550x550")
app.configure(bg="#e7e7e7")
app.resizable(False, False)

main_frame = tk.Frame(app, bg="#e7e7e7")
main_frame.pack(fill="both", expand=True, padx=15, pady=15)

# Seção Servidor
server_frame = tk.Frame(main_frame, bg="#ffffff", padx=20, pady=15)
server_frame.pack(fill="x", pady=(0, 10))

server_title = tk.Label(server_frame, text="Servidor de Configuração", 
                        font=("Segoe UI", 12, "bold"), bg="#ffffff")
server_title.pack(pady=(0, 12))

btn_toggle = tk.Button(
    server_frame,
    text="Ligar servidor",
    width=25,
    height=2,
    command=toggle_server,
    bg="#c8ffc8",
    relief="flat",
    font=("Segoe UI", 10)
)
btn_toggle.pack(pady=(0, 8))

btn_build = tk.Button(
    server_frame,
    text="Gerar novo build",
    width=25,
    height=1,
    command=build_project,
    bg="#e0e0e0",
    relief="flat",
    font=("Segoe UI", 9)
)
btn_build.pack(pady=(0, 5))

# Seção Processo ETL
etl_frame = tk.Frame(main_frame, bg="#ffffff", padx=20, pady=15)
etl_frame.pack(fill="x", pady=(0, 10))

etl_title = tk.Label(etl_frame, text="Processamento ETL", 
                     font=("Segoe UI", 12, "bold"), bg="#ffffff")
etl_title.pack(pady=(0, 12))

btn_processo = tk.Button(
    etl_frame,
    text="Iniciar Processo",
    width=25,
    height=2,
    command=lambda: threading.Thread(target=iniciar_processo, daemon=True).start(),
    bg="#aac8ff",
    relief="flat",
    font=("Segoe UI", 10, "bold")
)
btn_processo.pack(pady=(0, 10))

status_label = tk.Label(etl_frame, text="", font=("Segoe UI", 8), bg="#ffffff", fg="#666", wraplength=450)
status_label.pack(pady=(0, 5))

if os.path.exists(DIST_PATH) and os.listdir(DIST_PATH):
    status_label.config(text="✓ Pronto para iniciar", fg="green")
else:
    status_label.config(text="⚠ Build não encontrado (gere o build primeiro)", fg="orange")

# Botões de acesso rápido
bottom_frame = tk.Frame(main_frame, bg="#e7e7e7", padx=5, pady=10)
bottom_frame.pack(fill="x", pady=(10, 0))

btn_configs = tk.Button(
    bottom_frame,
    text="Abrir configs",
    width=18,
    command=open_configs,
    bg="#dcdcdc",
    relief="flat",
    font=("Segoe UI", 9)
)
btn_configs.pack(side="left", padx=5, expand=True)

btn_planilhas = tk.Button(
    bottom_frame,
    text="Abrir planilhas",
    width=18,
    command=open_planilhas,
    bg="#dcdcdc",
    relief="flat",
    font=("Segoe UI", 9)
)
btn_planilhas.pack(side="right", padx=5, expand=True)

def on_closing():
    stop_server()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
