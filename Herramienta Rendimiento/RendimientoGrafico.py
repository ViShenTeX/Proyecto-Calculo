from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button
from matplotlib.figure import Figure
from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from tkinter import ttk
import tkinter as tk
import numpy as np
import requests
import warnings
import sys

warnings.filterwarnings('ignore')
plt.style.use('dark_background')

# Configuración: URL del endpoint de usuarios anónimos
ENDPOINT_USUARIOS = 'http://127.0.0.1:8000/api/usuarios/anonimos/'

# Intervalos de actualización
intervalo_usuarios = 15000  # 15 segundos para consultar usuarios
intervalo_graficos = 15000  # 15 segundos para actualizar gráficos

# Variable global para pausar/reanudar
pausado = False

def obtener_usuarios_activos():
    try:
        response = requests.get(ENDPOINT_USUARIOS, timeout=2)
        if response.status_code == 200:
            data = response.json()
            return float(data.get('usuarios_anonimos', 0))
        else:
            return 0.0
    except Exception as e:
        print(f"[ERROR] No se pudo obtener usuarios del endpoint: {e}")
        return 0.0

ventana_tiempo_min = 2
ventana_tiempo_seg = ventana_tiempo_min * 60
TOPE_USUARIOS = 50
LIMITE_CRITICO = 80

tiempos, usuarios, velocidades, aceleraciones = [], [], [], []
servidor_detenido = False
tk_root = None
calc_status_var, calc_u_actual_var = None, None
v_subs_var, v_res_var = None, None
a_subs_var, a_res_var = None, None

def _quit():
    if tk_root:
        tk_root.quit()
        tk_root.destroy()
    sys.exit()

def mostrar_ayuda_derivadas():
    win_ayuda = tk.Toplevel(tk_root)
    win_ayuda.title("Ayuda: El Concepto de la Derivada")
    win_ayuda.configure(bg='#2d2d2d')
    win_ayuda.resizable(False, False)
    win_ayuda.transient(tk_root)

    main_frame = tk.Frame(win_ayuda, bg='#2d2d2d', padx=15, pady=15)
    main_frame.pack(fill=tk.BOTH, expand=True)

    font_h1 = ("Helvetica", 16, "bold"); font_h2 = ("Helvetica", 12, "bold")
    font_p = ("Helvetica", 11); font_formula = ("Consolas", 11, "italic")
    color_texto = "#ffffff"; color_bg = '#2d2d2d'

    # --- Título Principal ---
    tk.Label(main_frame, text="La Derivada: De la Teoría a la Práctica", font=font_h1, bg=color_bg, fg="white").pack(anchor="w", pady=(0, 15))

    # --- Parte 1: Definición Formal ---
    tk.Label(main_frame, text="Parte 1: La Definición Formal (Método de los 4 Pasos)", font=font_h2, bg=color_bg, fg="#4ecdc4").pack(anchor="w")
    tk.Label(main_frame, text="La derivada mide la 'pendiente' o tasa de cambio instantánea de una función. Se encuentra con este proceso:", font=font_p, bg=color_bg, fg=color_texto, wraplength=500, justify=tk.LEFT).pack(anchor="w", pady=5)
    
    steps_frame = tk.Frame(main_frame, bg=color_bg)
    steps_frame.pack(fill='x', anchor='w', pady=5, padx=10)
    
    tk.Label(steps_frame, text="Paso 1: Empezar con una función f(x).", font=font_p, bg=color_bg, fg=color_texto).grid(row=0, column=0, sticky='w')
    tk.Label(steps_frame, text="Ejemplo: f(x) = x²", font=font_formula, bg=color_bg, fg=color_texto).grid(row=0, column=1, sticky='w', padx=10)
    
    tk.Label(steps_frame, text="Paso 2: Evaluar la función en f(x + Δx).", font=font_p, bg=color_bg, fg=color_texto).grid(row=1, column=0, sticky='w')
    tk.Label(steps_frame, text="f(x + Δx) = (x + Δx)² = x² + 2xΔx + (Δx)²", font=font_formula, bg=color_bg, fg=color_texto).grid(row=1, column=1, sticky='w', padx=10)

    tk.Label(steps_frame, text="Paso 3: Calcular la diferencia Δy = f(x + Δx) - f(x).", font=font_p, bg=color_bg, fg=color_texto).grid(row=2, column=0, sticky='w')
    tk.Label(steps_frame, text="Δy = (x² + 2xΔx + (Δx)²) - x² = 2xΔx + (Δx)²", font=font_formula, bg=color_bg, fg=color_texto).grid(row=2, column=1, sticky='w', padx=10)

    tk.Label(steps_frame, text="Paso 4: Calcular el límite del cociente Δy/Δx.", font=font_p, bg=color_bg, fg=color_texto).grid(row=3, column=0, sticky='w')
    tk.Label(steps_frame, text="lim Δx→0 (2xΔx + (Δx)²)/Δx = lim Δx→0 (2x + Δx) = 2x", font=font_formula, bg=color_bg, fg=color_texto).grid(row=3, column=1, sticky='w', padx=10)
    
    ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=20)

    # --- Parte 2: Aproximación Numérica ---
    tk.Label(main_frame, text="Parte 2: La Aproximación Numérica (Lo que hace este Dashboard)", font=font_h2, bg=color_bg, fg="#ff9800").pack(anchor="w")
    tk.Label(main_frame, text="Nuestro programa no conoce la función 'U(t)' de forma algebraica. Solo tiene puntos de datos discretos (ej: 'a las 21:50 había 55 usuarios').\nPor lo tanto, no puede resolver el límite de forma simbólica.", font=font_p, bg=color_bg, fg=color_texto, wraplength=500, justify=tk.LEFT).pack(anchor="w", pady=5)
    tk.Label(main_frame, text="En lugar de eso, usa una aproximación numérica del Paso 4, asumiendo que el incremento de tiempo (Δt) es muy pequeño:", font=font_p, bg=color_bg, fg=color_texto, wraplength=500, justify=tk.LEFT).pack(anchor="w", pady=5)
    tk.Label(main_frame, text="Derivada ≈ Δy / Δx   --->   Velocidad ≈ (U₂ - U₁) / (t₂ - t₁)", font=font_formula, bg=color_bg, fg=color_texto).pack(anchor="w", pady=10)
    tk.Label(main_frame, text="Esta es la razón por la que el panel de cálculos muestra esa fórmula. Es la aplicación práctica y numérica de la definición formal de la derivada.", font=font_p, bg=color_bg, fg=color_texto, wraplength=500, justify=tk.LEFT).pack(anchor="w", pady=5)

def toggle_pausa(fig, axs, ax_button, btn_pausa):
    global pausado
    pausado = not pausado
    if pausado:
        btn_pausa.config(text='Reanudar', bg='#d32f2f')
    else:
        btn_pausa.config(text='Pausar', bg='#4CAF50')
        ciclo_de_actualizacion(fig, axs, ax_button)

def reiniciar_servidor(fig, axs, ax_button):
    global tiempos, usuarios, velocidades, aceleraciones, servidor_detenido
    tiempos, usuarios, velocidades, aceleraciones = [], [], [], []
    servidor_detenido = False
    if hasattr(obtener_usuarios_activos, "usuarios"): obtener_usuarios_activos.usuarios = 10.0
    if hasattr(ciclo_de_actualizacion, 'ultima_consulta'): delattr(ciclo_de_actualizacion, 'ultima_consulta')
    ax_button.set_visible(False)
    for ax in axs: ax.clear()
    status_label = tk_root.nametowidget('calc_frame.status_label')
    status_label.config(fg="lime")
    calc_status_var.set("Estado: REINICIADO")
    calc_u_actual_var.set("U(t) = Calculando...")
    v_subs_var.set("= ( ... ) / ( ... )"); v_res_var.set("= Calculando...")
    a_subs_var.set("= ( ... ) / ( ... )"); a_res_var.set("= Calculando...")
    ciclo_de_actualizacion(fig, axs, ax_button)
    fig.canvas.draw_idle()

def ciclo_de_actualizacion(fig, axs, ax_button):
    global servidor_detenido, tiempos, usuarios, velocidades, aceleraciones, pausado
    if pausado:
        return
    
    if servidor_detenido:
        ax_button.set_visible(True)
        tk_root.after(intervalo_graficos, lambda: ciclo_de_actualizacion(fig, axs, ax_button))
        return

    # Solo consultar usuarios cada 60 segundos
    tiempo_actual = datetime.now()
    if not hasattr(ciclo_de_actualizacion, 'ultima_consulta'):
        ciclo_de_actualizacion.ultima_consulta = tiempo_actual
        u = obtener_usuarios_activos()
        tiempos.append(tiempo_actual)
        usuarios.append(u)
    else:
        tiempo_desde_ultima = (tiempo_actual - ciclo_de_actualizacion.ultima_consulta).total_seconds()
        if tiempo_desde_ultima >= 15:  # 15 segundos
            u = obtener_usuarios_activos()
            tiempos.append(tiempo_actual)
            usuarios.append(u)
            ciclo_de_actualizacion.ultima_consulta = tiempo_actual
        else:
            # Usar el último valor conocido
            u = usuarios[-1] if usuarios else 0

    if u > LIMITE_CRITICO:
        servidor_detenido = True
        for ax in axs:
            ax.clear(); ax.set_facecolor('#1a1a1a')
            ax.text(0.5, 0.5, 'ERROR CRÍTICO\nServidor Detenido', ha='center', va='center',
                    transform=ax.transAxes, fontsize=16, fontweight='bold', color='#ffffff',
                    bbox=dict(boxstyle="round,pad=1", facecolor="#d32f2f"))
            ax.set_xticks([]); ax.set_yticks([])
        tk_root.after(intervalo_graficos, lambda: ciclo_de_actualizacion(fig, axs, ax_button))
        fig.canvas.draw_idle()
        return

    while tiempos and (tiempos[-1] - tiempos[0]).total_seconds() > ventana_tiempo_seg:
        tiempos.pop(0); usuarios.pop(0)
    
    if len(usuarios) >= 2:
        tiempos_sec = [t.timestamp() for t in tiempos]
        dt_sec = np.diff(tiempos_sec)
        du = np.diff(np.array(usuarios, dtype=float))
        
        velocidades_por_seg = np.divide(du, dt_sec, out=np.zeros_like(du, dtype=float), where=dt_sec!=0)
        velocidades = velocidades_por_seg * 60
        
        if len(velocidades) >= 2:
            dv = np.diff(velocidades)
            dt_acc = dt_sec[1:]
            aceleraciones_por_seg = np.divide(dv, dt_acc, out=np.zeros_like(dv, dtype=float), where=dt_acc!=0)
            aceleraciones = aceleraciones_por_seg * 60
        else:
            aceleraciones = []
    else:
        velocidades, aceleraciones = [], []

    for ax in axs:
        ax.clear(); ax.set_facecolor('#1a1a1a'); ax.grid(True, alpha=0.2, color='#404040')
        ax.tick_params(axis='x', colors='#a0a0a0'); ax.tick_params(axis='y', colors='#a0a0a0')
        for spine in ax.spines.values(): spine.set_color('#404040')

    color_usuarios = '#ff6b6b' if u > TOPE_USUARIOS else '#4ecdc4'
    axs[0].plot(tiempos, usuarios, color=color_usuarios, label='Usuarios Activos $U(t)$', linewidth=2.5)
    axs[0].axhline(y=TOPE_USUARIOS, color='#ff9800', linestyle='--', label=f'Límite ({TOPE_USUARIOS} u)')
    axs[0].axhline(y=LIMITE_CRITICO, color='#f44336', linestyle='-', label=f'Crítico ({LIMITE_CRITICO} u)')
    axs[0].set_title('Monitor de Usuarios', color='white'); axs[0].set_ylabel('Nº de Usuarios', color='white')
    axs[0].legend(loc='upper left', facecolor='#2d2d2d', edgecolor='#404040')

    if len(velocidades) > 0:
        axs[1].plot(tiempos[1:], velocidades, color='#81c784', label="Velocidad $U'(t)$", linewidth=2.5)
    axs[1].set_title('Velocidad (1ª Derivada)', color='white'); axs[1].set_ylabel('Usuarios / min', color='white')
    axs[1].legend(loc='upper left', facecolor='#2d2d2d', edgecolor='#404040')

    if len(aceleraciones) > 0:
        axs[2].plot(tiempos[2:], aceleraciones, color='#ff8a80', label="Aceleración $U''(t)$", linewidth=2.5)
        axs[2].axhline(0, color='#ffffff', linestyle='--', linewidth=1, alpha=0.5)
    axs[2].set_title('Aceleración (2ª Derivada)', color='white'); axs[2].set_ylabel('Usuarios / min²', color='white')
    axs[2].set_xlabel(f'Tiempo (Ventana de {ventana_tiempo_min} min)', color='white'); axs[2].legend(loc='upper left', facecolor='#2d2d2d', edgecolor='#404040')
    
    formatter = mdates.DateFormatter('%H:%M')
    axs[2].xaxis.set_major_formatter(formatter)
    
    if u > LIMITE_CRITICO: status, color = "CRÍTICO", "red"
    elif u > TOPE_USUARIOS: status, color = "ALERTA", "orange"
    else: status, color = "NORMAL", "lime"
    
    status_label = tk_root.nametowidget('calc_frame.status_label')
    status_label.config(fg=color); calc_status_var.set(f"Estado: {status}")
    calc_u_actual_var.set(f"U(t) actual = {u:.2f} usuarios")
    
    if len(velocidades) > 0:
        u2, u1 = usuarios[-1], usuarios[-2]; t2, t1 = tiempos[-1].timestamp(), tiempos[-2].timestamp()
        v_actual = velocidades[-1]
        v_subs_var.set(f"= (({u2:.2f} - {u1:.2f}) / ({(t2-t1):.3f} s)) * 60"); v_res_var.set(f"= {v_actual:+.3f} u/min")
    if len(aceleraciones) > 0:
        v_actual_2, v_actual_1 = velocidades[-1], velocidades[-2]; t2, t1 = tiempos[-1].timestamp(), tiempos[-2].timestamp()
        a_actual = aceleraciones[-1]
        a_subs_var.set(f"= (({v_actual_2:+.2f} - {v_actual_1:+.2f}) / ({(t2-t1):.3f} s)) * 60"); a_res_var.set(f"= {a_actual:+.3f} u/min²")
    
    fig.canvas.draw()
    tk_root.after(intervalo_graficos, lambda: ciclo_de_actualizacion(fig, axs, ax_button))

if __name__ == "__main__":
    tk_root = tk.Tk()
    tk_root.title("Dashboard Predictivo en Tiempo Real")
    tk_root.configure(bg='#1a1a1a')

    fig = Figure(figsize=(10, 8), dpi=100, facecolor='#1a1a1a')
    ax1 = fig.add_subplot(311); ax2 = fig.add_subplot(312, sharex=ax1); ax3 = fig.add_subplot(313, sharex=ax1)
    axs = [ax1, ax2, ax3]
    fig.tight_layout(rect=[0.05, 0.05, 0.98, 0.92])

    canvas = FigureCanvasTkAgg(fig, master=tk_root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    calc_frame = tk.Frame(tk_root, bg='#1a1a1a', padx=10, pady=10, name='calc_frame')
    calc_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

    calc_status_var = tk.StringVar(value="Estado: INICIANDO..."); calc_u_actual_var = tk.StringVar(value="U(t) = Calculando...")
    v_subs_var = tk.StringVar(value="= ( ... ) / ( ... )"); v_res_var = tk.StringVar(value="= Calculando...")
    a_subs_var = tk.StringVar(value="= ( ... ) / ( ... )"); a_res_var = tk.StringVar(value="= Calculando...")
    
    font_titulo = ("Helvetica", 14, "bold"); font_label = ("Consolas", 12); font_formula = ("Consolas", 12, "italic")
    font_proceso = ("Consolas", 12, "bold"); color_texto = "#ffffff"; color_bg = '#1a1a1a'; color_bg_frame = '#2d2d2d'

    tk.Label(calc_frame, textvariable=calc_status_var, font=font_titulo, bg=color_bg, fg="lime", name="status_label").pack(pady=(5, 10), anchor='w')
    ttk.Separator(calc_frame, orient='horizontal').pack(fill='x', pady=5)
    tk.Label(calc_frame, textvariable=calc_u_actual_var, font=font_label, bg=color_bg, fg=color_texto).pack(pady=5, anchor="w")

    v_frame = tk.Frame(calc_frame, bg=color_bg_frame, padx=10, pady=10); v_frame.pack(fill='x', pady=10, anchor='n')
    v_title_frame = tk.Frame(v_frame, bg=color_bg_frame)
    v_title_frame.pack(fill='x')
    tk.Label(v_title_frame, text="Velocidad (u/min)", font=font_titulo, bg=color_bg_frame, fg="#81c784").pack(side=tk.LEFT)
    tk.Button(v_title_frame, text="?", font=("Helvetica", 8, "bold"), command=mostrar_ayuda_derivadas, bg="#555", fg="white", width=2, bd=0).pack(side=tk.RIGHT)
    tk.Label(v_frame, text="U'(t) ≈ [(U₂-U₁)/(t₂-t₁)] * 60", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor="w", pady=(5,0))
    tk.Label(v_frame, textvariable=v_subs_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).pack(anchor="w")
    tk.Label(v_frame, textvariable=v_res_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).pack(anchor="w")

    a_frame = tk.Frame(calc_frame, bg=color_bg_frame, padx=10, pady=10); a_frame.pack(fill='x', pady=5, anchor='n')
    a_title_frame = tk.Frame(a_frame, bg=color_bg_frame)
    a_title_frame.pack(fill='x')
    tk.Label(a_title_frame, text="Aceleración (u/min²)", font=font_titulo, bg=color_bg_frame, fg="#ff8a80").pack(side=tk.LEFT)
    tk.Button(a_title_frame, text="?", font=("Helvetica", 8, "bold"), command=mostrar_ayuda_derivadas, bg="#555", fg="white", width=2, bd=0).pack(side=tk.RIGHT)
    tk.Label(a_frame, text="U''(t) ≈ [(V₂-V₁)/(t₂-t₁)] * 60", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor="w", pady=(5,0))
    tk.Label(a_frame, textvariable=a_subs_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).pack(anchor="w")
    tk.Label(a_frame, textvariable=a_res_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).pack(anchor="w")
    
    ax_button = fig.add_axes([0.45, 0.01, 0.15, 0.05], zorder=10)
    btn_reiniciar = Button(ax_button, 'REINICIAR', color='#4CAF50', hovercolor='#45a049')
    btn_reiniciar.label.set_fontsize(10); btn_reiniciar.label.set_fontweight('bold')
    btn_reiniciar.on_clicked(lambda event: reiniciar_servidor(fig, axs, ax_button))
    ax_button.set_visible(False)

    # Botón de Pausar/Reanudar
    btn_pausa = tk.Button(calc_frame, text="Pausar", font=font_titulo, bg="#4CAF50", fg="white", command=lambda: toggle_pausa(fig, axs, ax_button, btn_pausa))
    btn_pausa.pack(pady=(10, 0), fill='x')

    tk_root.protocol("WM_DELETE_WINDOW", _quit)
    ciclo_de_actualizacion(fig, axs, ax_button)
    tk.mainloop()