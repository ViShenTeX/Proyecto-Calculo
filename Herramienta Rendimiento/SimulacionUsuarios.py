import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
from datetime import datetime

ENDPOINT_USUARIOS = 'http://127.0.0.1:8000/api/usuarios/anonimos/'
ENDPOINT_AGREGAR = 'http://127.0.0.1:8000/api/usuarios/anonimos/agregar/'
ENDPOINT_QUITAR = 'http://127.0.0.1:8000/api/usuarios/anonimos/quitar/'

class SimuladorUsuarios:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simulador Automático de Carga de Usuarios")
        self.root.configure(bg='#1a1a1a')
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        
        # --- Variables de estado ---
        self.usuarios_actuales_var = tk.StringVar(value="Calculando...")
        self.estado_conexion_var = tk.StringVar(value="Desconectado")
        self.estado_simulacion_var = tk.StringVar(value="Inactiva")
        
        self.simulacion_activa = False
        self.thread_simulacion = None
        
        self.setup_ui()
        self.iniciar_monitoreo_conexion()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='#1a1a1a', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Simulador Automático de Carga", 
                 font=("Helvetica", 18, "bold"), bg='#1a1a1a', fg="white").pack(pady=(0, 20))
        
        estado_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15, relief=tk.RIDGE, borderwidth=2)
        estado_frame.pack(fill='x', pady=(0, 15))
        tk.Label(estado_frame, text="Estado de Conexión API:", 
                 font=("Helvetica", 12, "bold"), bg='#2d2d2d', fg="#4ecdc4").pack(anchor='w')
        tk.Label(estado_frame, textvariable=self.estado_conexion_var,
                 font=("Consolas", 11), bg='#2d2d2d', fg="white").pack(anchor='w', pady=(5, 0))
        
        usuarios_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15, relief=tk.RIDGE, borderwidth=2)
        usuarios_frame.pack(fill='x', pady=(0, 15))
        tk.Label(usuarios_frame, text="Usuarios Anónimos Actuales:", 
                 font=("Helvetica", 12, "bold"), bg='#2d2d2d', fg="#81c784").pack(anchor='w')
        tk.Label(usuarios_frame, textvariable=self.usuarios_actuales_var,
                 font=("Consolas", 16, "bold"), bg='#2d2d2d', fg="white").pack(anchor='w', pady=(5, 0))
        
        controles_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15, relief=tk.RIDGE, borderwidth=2)
        controles_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(controles_frame, text="Control de Simulación:", 
                 font=("Helvetica", 12, "bold"), bg='#2d2d2d', fg="#ff9800").pack(anchor='w')
        
        self.btn_control = tk.Button(controles_frame, text="Iniciar Simulación Automática", font=("Helvetica", 11, "bold"),
                                     bg='#4CAF50', fg='white', command=self.toggle_simulacion,
                                     padx=15, pady=10)
        self.btn_control.pack(pady=(10, 10), fill='x')
        
        tk.Label(controles_frame, textvariable=self.estado_simulacion_var,
                 font=("Consolas", 11, "italic"), bg='#2d2d2d', fg="white").pack(anchor='w')

    def toggle_simulacion(self):
        self.simulacion_activa = not self.simulacion_activa
        
        if self.simulacion_activa:
            self.btn_control.config(text="Pausar Simulación", bg='#f44336')
       
            if self.thread_simulacion is None or not self.thread_simulacion.is_alive():
                self.thread_simulacion = threading.Thread(target=self.ejecutar_ciclo_automatico, daemon=True)
                self.thread_simulacion.start()
        else:
            self.btn_control.config(text="Iniciar Simulación Automática", bg='#4CAF50')
            self.estado_simulacion_var.set("Simulación en pausa...")

    def ejecutar_ciclo_automatico(self):
        direccion = "subiendo"
        
        while True:
            if not self.simulacion_activa:
             
                time.sleep(1)
                continue

            try:
                usuarios_actuales = self.obtener_usuarios_actuales()
                
                if direccion == "subiendo":
                    self.estado_simulacion_var.set(f"Agregando usuarios... (Actual: {usuarios_actuales})")
                    response = requests.post(ENDPOINT_AGREGAR, timeout=2)
                    if response.status_code != 200:
                        print("Error al agregar usuario, pausando.")
                        self.simulacion_activa = False 
                    if usuarios_actuales >= 90:
                        direccion = "bajando"

                elif direccion == "bajando":
                    self.estado_simulacion_var.set(f"Quitando usuarios... (Actual: {usuarios_actuales})")
                    response = requests.post(ENDPOINT_QUITAR, timeout=2)
                    if response.status_code != 200:
                        print("Error al quitar usuario, pausando.")
                        self.simulacion_activa = False #
                    if usuarios_actuales <= 5:
                        direccion = "subiendo"
                
                time.sleep(0.2) 

            except Exception as e:
                print(f"Error en el ciclo de simulación: {e}. Pausando.")
                self.simulacion_activa = False

    def obtener_usuarios_actuales(self):
        try:
            response = requests.get(ENDPOINT_USUARIOS, timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get('usuarios_anonimos', 0)
            return 0
        except Exception:
            return 0
    
    def monitorear_conexion_loop(self):
        while True:
            try:
                response = requests.get(ENDPOINT_USUARIOS, timeout=2)
                if response.status_code == 200:
                    self.estado_conexion_var.set("Conectado ✓")
                    data = response.json()
                    usuarios = data.get('usuarios_anonimos', 'N/A')
                    self.usuarios_actuales_var.set(str(usuarios))
                else:
                    self.estado_conexion_var.set("Error de conexión ✗")
            except Exception:
                self.estado_conexion_var.set("Desconectado ✗")
            
            time.sleep(2) #
    
    def iniciar_monitoreo_conexion(self):
        thread = threading.Thread(target=self.monitorear_conexion_loop, daemon=True)
        thread.start()
    
    def ejecutar(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimuladorUsuarios()
    app.ejecutar()
