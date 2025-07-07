from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button
from matplotlib.figure import Figure
from datetime import datetime, timedelta
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


ENDPOINT_USUARIOS = 'http://127.0.0.1:8000/api/usuarios/anonimos/'

intervalo_graficos = 1000  # ms

# Variables globales
pausado = False
ventana_tiempo_min = 2
ventana_tiempo_seg = ventana_tiempo_min * 60
TOPE_USUARIOS = 50
LIMITE_CRITICO = 80

tiempos, usuarios, velocidades, aceleraciones = [], [], [], []
servidor_detenido = False
reporte_generado = False

tk_root = None
calc_status_var, calc_u_actual_var = None, None
v_subs_var, v_res_var = None, None
a_subs_var, a_res_var = None, None

def generar_reporte_incidente(datos):
    """
    Crea una nueva ventana Toplevel con el reporte del incidente,
    incluyendo una línea vertical que marca el momento del crash.
    """
    report_win = tk.Toplevel(tk_root)
    report_win.title("Reporte de Incidente Crítico")
    report_win.configure(bg='#1a1a1a')
    report_win.geometry("900x700")

    main_frame = tk.Frame(report_win, bg='#1a1a1a', padx=15, pady=15)
    main_frame.pack(fill=tk.BOTH, expand=True)

    info_frame = tk.Frame(main_frame, bg='#2d2d2d', padx=10, pady=10)
    info_frame.pack(fill='x', pady=(0, 10))
    
    tk.Label(info_frame, text="REPORTE DE INCIDENTE CRÍTICO", font=("Helvetica", 16, "bold"), bg='#2d2d2d', fg='#f44336').pack(anchor='w')
    tk.Label(info_frame, text=f"Hora del incidente: {datos['timestamp']:%Y-%m-%d %H:%M:%S}", font=("Consolas", 11), bg='#2d2d2d', fg='white').pack(anchor='w')
    tk.Label(info_frame, text=f"Límite Crítico Superado: {datos['u_critico']:.2f} / {LIMITE_CRITICO} usuarios", font=("Consolas", 11, "bold"), bg='#2d2d2d', fg='orange').pack(anchor='w')
    
    tk.Label(info_frame, text=f"Velocidad al momento del colapso (U'(t)): {datos['v_critica']:+.3f} u/min", font=("Consolas", 11), bg='#2d2d2d', fg='white').pack(anchor='w')
    tk.Label(info_frame, text=f"Aceleración al momento del colapso (U''(t)): {datos['a_critica']:+.3f} u/min²", font=("Consolas", 11), bg='#2d2d2d', fg='white').pack(anchor='w')

    fig_reporte = Figure(figsize=(8, 6), dpi=100, facecolor='#1a1a1a')
    ax1_r = fig_reporte.add_subplot(311)
    ax2_r = fig_reporte.add_subplot(312, sharex=ax1_r)
    ax3_r = fig_reporte.add_subplot(313, sharex=ax1_r)
    
    axes_reporte = [ax1_r, ax2_r, ax3_r]
    for ax in axes_reporte:
        ax.set_facecolor('#1a1a1a'); ax.grid(True, alpha=0.2, color='#404040')
        ax.tick_params(axis='x', colors='#a0a0a0'); ax.tick_params(axis='y', colors='#a0a0a0')
        for spine in ax.spines.values(): spine.set_color('#404040')

    # --- Gráfico 1: Usuarios y Recta Tangente (Velocidad) ---
    ax1_r.plot(datos['tiempos'], datos['usuarios'], color='#4ecdc4', label='Usuarios $U(t)$')
    ax1_r.plot(datos['timestamp'], datos['u_critico'], 'o', color='yellow', markersize=8, label='Punto Crítico')
    v_critica_por_seg = datos['v_critica'] / 60.0
    t_critico = datos['timestamp']
    u_critico = datos['u_critico']
    delta_t = timedelta(seconds=45)
    t_tangente = [t_critico - delta_t, t_critico + delta_t]
    u_tangente = [u_critico - v_critica_por_seg * 45, u_critico + v_critica_por_seg * 45]
    ax1_r.plot(t_tangente, u_tangente, color='#ff6b6b', linestyle='--', linewidth=2, label=f'Recta Tangente (Velocidad: {datos["v_critica"]:.2f} u/min)')
    ax1_r.set_title('Historial de Usuarios y Velocidad Instantánea', color='white')
    
    # --- Gráfico 2: Velocidad y Recta Tangente (Aceleración) ---
    if len(datos['velocidades']) > 0:
        ax2_r.plot(datos['tiempos'][1:], datos['velocidades'], color='#81c784', label="Velocidad $U'(t)$")
        v_critica_val = datos['v_critica']
        ax2_r.plot(t_critico, v_critica_val, 'o', color='yellow', markersize=8)
        a_critica_por_seg_min = datos['a_critica'] / 60.0
        v_tangente = [v_critica_val - a_critica_por_seg_min * 45, v_critica_val + a_critica_por_seg_min * 45]
        ax2_r.plot(t_tangente, v_tangente, color='#ff9800', linestyle='--', linewidth=2, label=f'Recta Tangente (Aceleración: {datos["a_critica"]:.2f} u/min²)')
    ax2_r.set_title('Historial de Velocidad y Aceleración Instantánea', color='white')

    # --- Gráfico 3: Aceleración ---
    if len(datos['aceleraciones']) > 0:
        ax3_r.plot(datos['tiempos'][2:], datos['aceleraciones'], color='#ff8a80', label="Aceleración $U''(t)$")
        ax3_r.plot(t_critico, datos['a_critica'], 'o', color='yellow', markersize=8)
    ax3_r.set_title('Historial de Aceleración', color='white')
    
    for ax in axes_reporte:
        ax.legend(loc='upper left', facecolor='#2d2d2d', edgecolor='#404040', fontsize='small')
    
    fig_reporte.tight_layout()
    
    canvas_reporte = FigureCanvasTkAgg(fig_reporte, master=main_frame)
    canvas_reporte.draw()
    canvas_reporte.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)

    report_win.canvas = canvas_reporte

    tk.Button(main_frame, text="Cerrar Reporte", command=report_win.destroy, bg='#d32f2f', fg='white', font=("Helvetica", 10, "bold")).pack()

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

def _quit():
    if tk_root:
        tk_root.quit()
        tk_root.destroy()
    sys.exit()

def mostrar_ayuda_derivadas():
    win_ayuda = tk.Toplevel(tk_root)
    win_ayuda.title("Ayuda: ¿Cómo se calculan las derivadas?")
    win_ayuda.configure(bg='#2d2d2d')
    win_ayuda.resizable(False, False)
    win_ayuda.transient(tk_root)

    main_frame = tk.Frame(win_ayuda, bg='#2d2d2d', padx=15, pady=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    font_h1 = ("Helvetica", 16, "bold")
    font_h2 = ("Helvetica", 12, "bold")
    font_h3 = ("Helvetica", 10, "bold")
    font_p = ("Helvetica", 10)
    font_formula = ("Consolas", 10, "italic")
    color_texto = "#ffffff"
    color_bg = '#2d2d2d'
    color_bg_frame = '#3c3c3c'
    color_v = '#81c784'
    color_a = '#ff8a80'

    tk.Label(main_frame, text="La Derivada: De la Teoría a la Práctica", font=font_h1, bg=color_bg, fg="white").pack(anchor="w", pady=(0, 15))
    tk.Label(main_frame, text="Este programa no conoce la función U(t) de forma algebraica (ej: x²). Solo tiene puntos de datos discretos (ej: 'a las 21:50 había 55 usuarios').\nPor lo tanto, usa una aproximación numérica para calcular la 'pendiente' o tasa de cambio en cada momento.", font=font_p, bg=color_bg, fg=color_texto, wraplength=600, justify=tk.LEFT).pack(anchor="w", pady=5)
    
    ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)

    # --- CÁLCULO DE LA 1RA DERIVADA (VELOCIDAD) ---
    tk.Label(main_frame, text="Cálculo de la 1ª Derivada (Velocidad)", font=font_h2, bg=color_bg, fg=color_v).pack(anchor="w", pady=(5,5))
    
    v_frame = tk.Frame(main_frame, bg=color_bg_frame, padx=10, pady=10)
    v_frame.pack(fill='x', pady=5)

    tk.Label(v_frame, text="Paso 1: Tomar dos puntos de datos consecutivos.", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w')
    tk.Label(v_frame, text="Punto 1: (t₁, U₁)  y  Punto 2: (t₂, U₂)", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)
    
    tk.Label(v_frame, text="Paso 2: Calcular el cambio en Usuarios (ΔU).", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(v_frame, text="ΔU = U₂ - U₁", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    tk.Label(v_frame, text="Paso 3: Calcular el cambio en Tiempo en segundos (Δt).", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(v_frame, text="Δt = t₂ - t₁", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    tk.Label(v_frame, text="Paso 4: Calcular la velocidad en 'usuarios por segundo'.", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(v_frame, text="Velocidad (u/s) ≈ ΔU / Δt", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    tk.Label(v_frame, text="Paso 5: Convertir a 'usuarios por minuto' para el reporte.", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(v_frame, text="U'(t) = Velocidad (u/min) = Velocidad (u/s) * 60", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    # --- CÁLCULO DE LA 2DA DERIVADA (ACELERACIÓN) ---
    tk.Label(main_frame, text="Cálculo de la 2ª Derivada (Aceleración)", font=font_h2, bg=color_bg, fg=color_a).pack(anchor="w", pady=(15,5))
    
    a_frame = tk.Frame(main_frame, bg=color_bg_frame, padx=10, pady=10)
    a_frame.pack(fill='x', pady=5)

    tk.Label(a_frame, text="Paso 1: Tomar dos valores de velocidad consecutivos.", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w')
    tk.Label(a_frame, text="Velocidad 1: V₁  y  Velocidad 2: V₂", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    tk.Label(a_frame, text="Paso 2: Calcular el cambio en Velocidad (ΔV).", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(a_frame, text="ΔV = V₂ - V₁", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    tk.Label(a_frame, text="Paso 3: Usar el mismo cambio de tiempo (Δt) del paso anterior.", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(a_frame, text="Δt = t₂ - t₁", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    tk.Label(a_frame, text="Paso 4: Calcular la aceleración en 'usuarios por minuto por segundo'.", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(a_frame, text="Aceleración (u/min/s) ≈ ΔV / Δt", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

    tk.Label(a_frame, text="Paso 5: Convertir a 'usuarios por minuto al cuadrado' para el reporte.", font=font_h3, bg=color_bg_frame, fg=color_texto).pack(anchor='w', pady=(10,0))
    tk.Label(a_frame, text="U''(t) = Aceleración (u/min²) = Aceleración (u/min/s) * 60", font=font_formula, bg=color_bg_frame, fg=color_texto).pack(anchor='w', padx=10)

def toggle_pausa(fig, axs, ax_button, btn_pausa):
    global pausado
    pausado = not pausado
    if pausado:
        btn_pausa.config(text='Reanudar', bg='#d32f2f')
    else:
        btn_pausa.config(text='Pausar', bg='#4CAF50')
        ciclo_de_actualizacion(fig, axs, ax_button)

def reiniciar_servidor(fig, axs, ax_button):
    global tiempos, usuarios, velocidades, aceleraciones, servidor_detenido, reporte_generado
    tiempos, usuarios, velocidades, aceleraciones = [], [], [], []
    servidor_detenido = False
    reporte_generado = False
    if hasattr(obtener_usuarios_activos, "usuarios"): obtener_usuarios_activos.usuarios = 10.0
    if hasattr(ciclo_de_actualizacion, 'ultima_consulta'): delattr(ciclo_de_actualizacion, 'ultima_consulta')
    ax_button.set_visible(False)
    for ax in axs: ax.clear()
    status_label = tk_root.nametowidget('calc_frame.status_label')
    status_label.config(fg="lime")
    calc_status_var.set("Estado: REINICIADO")
    calc_u_actual_var.set("U(t) = Calculando...")
    # --- MODIFICACIÓN INICIA ---
    v_subs_var.set("(( ... - ... ) / ( ... s)) * 60"); v_res_var.set("Calculando...")
    a_subs_var.set("(( ... - ... ) / ( ... s)) * 60"); a_res_var.set("Calculando...")
    # --- MODIFICACIÓN TERMINA ---
    ciclo_de_actualizacion(fig, axs, ax_button)
    fig.canvas.draw_idle()

def ciclo_de_actualizacion(fig, axs, ax_button):
    global servidor_detenido, tiempos, usuarios, velocidades, aceleraciones, pausado, reporte_generado
    if pausado:
        return
    
    if servidor_detenido:
        ax_button.set_visible(True)
        tk_root.after(intervalo_graficos, lambda: ciclo_de_actualizacion(fig, axs, ax_button))
        return

    u = obtener_usuarios_activos()
    tiempos.append(datetime.now())
    usuarios.append(u)

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
            aceleraciones = np.array([])
    else:
        velocidades, aceleraciones = np.array([]), np.array([])


    if u > LIMITE_CRITICO:
        servidor_detenido = True
        if not reporte_generado:
            reporte_generado = True
            datos_incidente = {
                "timestamp": tiempos[-1],
                "u_critico": u,
                "v_critica": velocidades[-1] if len(velocidades) > 0 else 0,
                "a_critica": aceleraciones[-1] if len(aceleraciones) > 0 else 0,
                "tiempos": list(tiempos),
                "usuarios": list(usuarios),
                "velocidades": list(velocidades),
                "aceleraciones": list(aceleraciones)
            }
            generar_reporte_incidente(datos_incidente)

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
        if len(velocidades) > 0: velocidades = np.delete(velocidades, 0)
        if len(aceleraciones) > 0: aceleraciones = np.delete(aceleraciones, 0)
    
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
    
    # --- MODIFICACIÓN INICIA ---
    if len(velocidades) > 0:
        u2, u1 = usuarios[-1], usuarios[-2]
        t2, t1 = tiempos[-1].timestamp(), tiempos[-2].timestamp()
        v_actual = velocidades[-1]
        v_subs_var.set(f"(({u2:.2f} - {u1:.2f}) / ({t2 - t1:.3f} s)) * 60")
        v_res_var.set(f"{v_actual:+.3f} u/min")
    if len(aceleraciones) > 0 and len(tiempos) >= 3:
        v_actual_2, v_actual_1 = velocidades[-1], velocidades[-2]
        # Usamos los tiempos correspondientes al intervalo de velocidades
        t_acc_2, t_acc_1 = tiempos[-2].timestamp(), tiempos[-3].timestamp()
        a_actual = aceleraciones[-1]
        a_subs_var.set(f"(({v_actual_2:+.2f} - {v_actual_1:+.2f}) / ({t_acc_2 - t_acc_1:.3f} s)) * 60")
        a_res_var.set(f"{a_actual:+.3f} u/min²")
    # --- MODIFICACIÓN TERMINA ---

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

    # --- MODIFICACIÓN INICIA ---
    calc_status_var = tk.StringVar(value="Estado: INICIANDO...")
    calc_u_actual_var = tk.StringVar(value="U(t) = Calculando...")
    v_subs_var = tk.StringVar(value="(( ... - ... ) / ( ... s)) * 60")
    v_res_var = tk.StringVar(value="Calculando...")
    a_subs_var = tk.StringVar(value="(( ... - ... ) / ( ... s)) * 60")
    a_res_var = tk.StringVar(value="Calculando...")
    
    font_titulo = ("Helvetica", 14, "bold"); font_label = ("Consolas", 12); font_formula = ("Consolas", 11)
    font_proceso = ("Consolas", 12, "bold"); color_texto = "#ffffff"; color_bg = '#1a1a1a'; color_bg_frame = '#2d2d2d'

    tk.Label(calc_frame, textvariable=calc_status_var, font=font_titulo, bg=color_bg, fg="lime", name="status_label").pack(pady=(5, 10), anchor='w')
    ttk.Separator(calc_frame, orient='horizontal').pack(fill='x', pady=5)
    tk.Label(calc_frame, textvariable=calc_u_actual_var, font=font_label, bg=color_bg, fg=color_texto).pack(pady=5, anchor="w")

    # --- Frame de Velocidad (Nuevo layout con grid) ---
    v_frame = tk.Frame(calc_frame, bg=color_bg_frame, padx=10, pady=10); v_frame.pack(fill='x', pady=10, anchor='n')
    v_frame.grid_columnconfigure(0, minsize=45)
    v_frame.grid_columnconfigure(1, minsize=20)
    v_frame.grid_columnconfigure(2, weight=1)

    v_title_frame = tk.Frame(v_frame, bg=color_bg_frame)
    v_title_frame.grid(row=0, column=0, columnspan=3, sticky='ew')
    tk.Label(v_title_frame, text="Velocidad (u/min)", font=font_titulo, bg=color_bg_frame, fg="#81c784").pack(side=tk.LEFT)
    tk.Button(v_title_frame, text="?", font=("Helvetica", 8, "bold"), command=mostrar_ayuda_derivadas, bg="#555", fg="white", width=2, bd=0).pack(side=tk.RIGHT)
    
    tk.Label(v_frame, text="U'(t)", font=font_formula, bg=color_bg_frame, fg=color_texto).grid(row=1, column=0, sticky='w')
    tk.Label(v_frame, text="≈", font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=1, column=1)
    tk.Label(v_frame, text="[(U₂-U₁)/(t₂-t₁)] * 60", font=font_formula, bg=color_bg_frame, fg=color_texto).grid(row=1, column=2, sticky='w')
    
    tk.Label(v_frame, text="=", font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=2, column=1)
    tk.Label(v_frame, textvariable=v_subs_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=2, column=2, sticky='w')

    tk.Label(v_frame, text="=", font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=3, column=1)
    tk.Label(v_frame, textvariable=v_res_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=3, column=2, sticky='w')

    # --- Frame de Aceleración (Nuevo layout con grid) ---
    a_frame = tk.Frame(calc_frame, bg=color_bg_frame, padx=10, pady=10); a_frame.pack(fill='x', pady=5, anchor='n')
    a_frame.grid_columnconfigure(0, minsize=45)
    a_frame.grid_columnconfigure(1, minsize=20)
    a_frame.grid_columnconfigure(2, weight=1)

    a_title_frame = tk.Frame(a_frame, bg=color_bg_frame)
    a_title_frame.grid(row=0, column=0, columnspan=3, sticky='ew')
    tk.Label(a_title_frame, text="Aceleración (u/min²)", font=font_titulo, bg=color_bg_frame, fg="#ff8a80").pack(side=tk.LEFT)
    tk.Button(a_title_frame, text="?", font=("Helvetica", 8, "bold"), command=mostrar_ayuda_derivadas, bg="#555", fg="white", width=2, bd=0).pack(side=tk.RIGHT)

    tk.Label(a_frame, text="U''(t)", font=font_formula, bg=color_bg_frame, fg=color_texto).grid(row=1, column=0, sticky='w')
    tk.Label(a_frame, text="≈", font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=1, column=1)
    tk.Label(a_frame, text="[(V₂-V₁)/(t₂-t₁)] * 60", font=font_formula, bg=color_bg_frame, fg=color_texto).grid(row=1, column=2, sticky='w')

    tk.Label(a_frame, text="=", font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=2, column=1)
    tk.Label(a_frame, textvariable=a_subs_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=2, column=2, sticky='w')

    tk.Label(a_frame, text="=", font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=3, column=1)
    tk.Label(a_frame, textvariable=a_res_var, font=font_proceso, bg=color_bg_frame, fg=color_texto).grid(row=3, column=2, sticky='w')
    # --- MODIFICACIÓN TERMINA ---

    ax_button = fig.add_axes([0.45, 0.01, 0.15, 0.05], zorder=10)
    btn_reiniciar = Button(ax_button, 'REINICIAR', color='#4CAF50', hovercolor='#45a049')
    btn_reiniciar.label.set_fontsize(10); btn_reiniciar.label.set_fontweight('bold')
    btn_reiniciar.on_clicked(lambda event: reiniciar_servidor(fig, axs, ax_button))
    ax_button.set_visible(False)

    btn_pausa = tk.Button(calc_frame, text="Pausar", font=font_titulo, bg="#4CAF50", fg="white", command=lambda: toggle_pausa(fig, axs, ax_button, btn_pausa))
    btn_pausa.pack(pady=(10, 0), fill='x')

    tk_root.protocol("WM_DELETE_WINDOW", _quit)
    ciclo_de_actualizacion(fig, axs, ax_button)
    tk.mainloop()