import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
from datetime import datetime

# Configuración: URL del endpoint de usuarios anónimos
ENDPOINT_USUARIOS = 'http://127.0.0.1:8000/api/usuarios/anonimos/'
ENDPOINT_AGREGAR = 'http://127.0.0.1:8000/api/usuarios/anonimos/agregar/'
ENDPOINT_QUITAR = 'http://127.0.0.1:8000/api/usuarios/anonimos/quitar/'

class SimuladorUsuarios:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simulador de Usuarios Anónimos")
        self.root.configure(bg='#1a1a1a')
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        
        # Variables
        self.cantidad_var = tk.StringVar(value="1")
        self.usuarios_actuales_var = tk.StringVar(value="0")
        self.estado_conexion_var = tk.StringVar(value="Desconectado")
        
        self.setup_ui()
        self.iniciar_monitoreo()
        
    def setup_ui(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1a1a1a', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(main_frame, text="Simulador de Usuarios Anónimos", 
                         font=("Helvetica", 18, "bold"), bg='#1a1a1a', fg="white")
        titulo.pack(pady=(0, 20))
        
        # Frame de estado de conexión
        estado_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15)
        estado_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(estado_frame, text="Estado de Conexión:", 
                font=("Helvetica", 12, "bold"), bg='#2d2d2d', fg="#4ecdc4").pack(anchor='w')
        tk.Label(estado_frame, textvariable=self.estado_conexion_var,
                font=("Consolas", 11), bg='#2d2d2d', fg="white").pack(anchor='w', pady=(5, 0))
        
        # Frame de usuarios actuales
        usuarios_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15)
        usuarios_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(usuarios_frame, text="Usuarios Anónimos Actuales:", 
                font=("Helvetica", 12, "bold"), bg='#2d2d2d', fg="#81c784").pack(anchor='w')
        tk.Label(usuarios_frame, textvariable=self.usuarios_actuales_var,
                font=("Consolas", 16, "bold"), bg='#2d2d2d', fg="white").pack(anchor='w', pady=(5, 0))
        
        # Frame de controles
        controles_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=15, pady=15)
        controles_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(controles_frame, text="Cantidad de Usuarios:", 
                font=("Helvetica", 12, "bold"), bg='#2d2d2d', fg="white").pack(anchor='w')
        
        # Frame para entrada y botones
        entrada_frame = tk.Frame(controles_frame, bg='#2d2d2d')
        entrada_frame.pack(fill='x', pady=(10, 0))
        
        # Entrada de cantidad
        tk.Entry(entrada_frame, textvariable=self.cantidad_var, font=("Consolas", 12),
                bg='#404040', fg='white', insertbackground='white', width=10).pack(side=tk.LEFT, padx=(0, 10))
        
        # Botones
        tk.Button(entrada_frame, text="Agregar Usuarios", font=("Helvetica", 11, "bold"),
                 bg='#4CAF50', fg='white', command=self.agregar_usuarios,
                 padx=15, pady=5).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(entrada_frame, text="Quitar Usuarios", font=("Helvetica", 11, "bold"),
                 bg='#f44336', fg='white', command=self.quitar_usuarios,
                 padx=15, pady=5).pack(side=tk.LEFT)
        

    
    def obtener_usuarios_actuales(self):
        try:
            response = requests.get(ENDPOINT_USUARIOS, timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get('usuarios_anonimos', 0)
            else:
                return 0
        except Exception as e:
            return 0
    
    def actualizar_estado_conexion(self):
        try:
            response = requests.get(ENDPOINT_USUARIOS, timeout=2)
            if response.status_code == 200:
                self.estado_conexion_var.set("Conectado ✓")
                return True
            else:
                self.estado_conexion_var.set("Error de conexión ✗")
                return False
        except Exception as e:
            self.estado_conexion_var.set("Desconectado ✗")
            return False
    
    def agregar_usuarios(self):
        try:
            cantidad = int(self.cantidad_var.get())
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                return
            
            # Agregar usuarios uno por uno
            for i in range(cantidad):
                response = requests.post(ENDPOINT_AGREGAR, timeout=2)
                if response.status_code != 200:
                    raise Exception(f"Error al agregar usuario {i+1}")
                time.sleep(0.1)  # Pequeña pausa entre peticiones
            
            self.actualizar_usuarios_actuales()
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresa un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron agregar usuarios: {str(e)}")
    
    def quitar_usuarios(self):
        try:
            cantidad = int(self.cantidad_var.get())
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                return
            
            # Quitar usuarios uno por uno
            for i in range(cantidad):
                response = requests.post(ENDPOINT_QUITAR, timeout=2)
                if response.status_code != 200:
                    raise Exception(f"Error al quitar usuario {i+1}")
                time.sleep(0.1)  # Pequeña pausa entre peticiones
            
            self.actualizar_usuarios_actuales()
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingresa un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron quitar usuarios: {str(e)}")
    
    def actualizar_usuarios_actuales(self):
        usuarios = self.obtener_usuarios_actuales()
        self.usuarios_actuales_var.set(str(usuarios))
    

    
    def monitorear_conexion(self):
        while True:
            self.actualizar_estado_conexion()
            self.actualizar_usuarios_actuales()
            time.sleep(15)  # Actualizar cada 15 segundos
    
    def iniciar_monitoreo(self):
        # Iniciar monitoreo en un hilo separado
        thread = threading.Thread(target=self.monitorear_conexion, daemon=True)
        thread.start()
    
    def ejecutar(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimuladorUsuarios()
    app.ejecutar()
