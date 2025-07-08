import tkinter as tk
from tkinter import messagebox
import requests
import threading
import time

ENDPOINT_USUARIOS = 'http://127.0.0.1:8000/api/usuarios/anonimos/'
ENDPOINT_AGREGAR = 'http://127.0.0.1:8000/api/usuarios/anonimos/agregar/'
ENDPOINT_QUITAR = 'http://127.0.0.1:8000/api/usuarios/anonimos/quitar/'

class SimuladorUsuarios:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simulador Automático de Carga de Usuarios")
        self.root.configure(bg='#1a1a1a')
        self.root.geometry("600x500")
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
        
        # Botón para aumentar usuarios manualmente (ahora inicia/detiene ciclo automático de aumento)
        self.btn_agregar = tk.Button(controles_frame, text="Iniciar Aumento Automático (+)", font=("Helvetica", 10, "bold"),
                                     bg='#388e3c', fg='white', command=self.toggle_aumentar,
                                     padx=10, pady=6)
        self.btn_agregar.pack(pady=(10, 5), fill='x')

        # Botón para disminuir usuarios manualmente (ahora inicia/detiene ciclo automático de disminución)
        self.btn_quitar = tk.Button(controles_frame, text="Iniciar Disminución Automática (-)", font=("Helvetica", 10, "bold"),
                                    bg='#d32f2f', fg='white', command=self.toggle_disminuir,
                                    padx=10, pady=6)
        self.btn_quitar.pack(pady=(0, 10), fill='x')
        
        tk.Label(controles_frame, textvariable=self.estado_simulacion_var,
                 font=("Consolas", 11, "italic"), bg='#2d2d2d', fg="white").pack(anchor='w')

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

    def toggle_aumentar(self):
        if hasattr(self, 'accion_actual') and self.accion_actual == 'aumentar':
            # Si ya está aumentando, detener
            self.accion_actual = None
            self.simulacion_activa = False
            self.btn_agregar.config(text="Iniciar Aumento Automático (+)", bg='#388e3c')
            self.estado_simulacion_var.set("Aumento detenido.")
        else:
            # Si estaba disminuyendo, detener ese hilo
            self.simulacion_activa = False
            self.accion_actual = 'aumentar'
            self.btn_agregar.config(text="Detener Aumento Automático", bg='#f44336')
            self.btn_quitar.config(text="Iniciar Disminución Automática (-)", bg='#d32f2f')
            self.estado_simulacion_var.set("Aumentando usuarios automáticamente...")
            threading.Thread(target=self.ciclo_aumentar, daemon=True).start()

    def toggle_disminuir(self):
        if hasattr(self, 'accion_actual') and self.accion_actual == 'disminuir':
            # Si ya está disminuyendo, detener
            self.accion_actual = None
            self.simulacion_activa = False
            self.btn_quitar.config(text="Iniciar Disminución Automática (-)", bg='#d32f2f')
            self.estado_simulacion_var.set("Disminución detenida.")
        else:
            # Si estaba aumentando, detener ese hilo
            self.simulacion_activa = False
            self.accion_actual = 'disminuir'
            self.btn_quitar.config(text="Detener Disminución Automática", bg='#f44336')
            self.btn_agregar.config(text="Iniciar Aumento Automático (+)", bg='#388e3c')
            self.estado_simulacion_var.set("Disminuyendo usuarios automáticamente...")
            threading.Thread(target=self.ciclo_disminuir, daemon=True).start()

    def ciclo_aumentar(self):
        self.simulacion_activa = True
        while self.simulacion_activa and getattr(self, 'accion_actual', None) == 'aumentar':
            try:
                response = requests.post(ENDPOINT_AGREGAR, timeout=2)
                if response.status_code != 200:
                    self.estado_simulacion_var.set("Error al aumentar usuario. Deteniendo.")
                    break
            except Exception as e:
                self.estado_simulacion_var.set(f"Error: {e}. Deteniendo.")
                break
            time.sleep(0.2)  # velocidad de aumento
        self.simulacion_activa = False
        self.btn_agregar.config(text="Iniciar Aumento Automático (+)", bg='#388e3c')
        self.accion_actual = None

    def ciclo_disminuir(self):
        self.simulacion_activa = True
        while self.simulacion_activa and getattr(self, 'accion_actual', None) == 'disminuir':
            try:
                response = requests.post(ENDPOINT_QUITAR, timeout=2)
                if response.status_code != 200:
                    self.estado_simulacion_var.set("Error al disminuir usuario. Deteniendo.")
                    break
            except Exception as e:
                self.estado_simulacion_var.set(f"Error: {e}. Deteniendo.")
                break
            time.sleep(0.2)  # velocidad igualada a la de aumento
        self.simulacion_activa = False
        self.btn_quitar.config(text="Iniciar Disminución Automática (-)", bg='#d32f2f')
        self.accion_actual = None

if __name__ == "__main__":
    app = SimuladorUsuarios()
    app.ejecutar()
