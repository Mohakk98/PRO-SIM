import customtkinter as ctk

class TabBuilder:
    """Générateur d'onglets de configuration avec couplage réactif en temps réel pour PRO-SIM v5.2."""
    @staticmethod
    def build_puits_tab(tab, app):
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        frame_input = ctk.CTkScrollableFrame(tab, width=340)
        frame_input.grid(row=0, column=0, padx=10, pady=10, sticky="nsw")
        
        ctk.CTkLabel(frame_input, text="RESERVOIR & WELL GEOMETRY", font=("Arial", 12, "bold")).pack(pady=5)
        TabBuilder.creer_slider(frame_input, "Reservoir Pressure (psi)", app.pr, 1000, 5000, app, "nodal")
        TabBuilder.creer_slider(frame_input, "Productivity Index (PI)", app.ip, 0.5, 5.0, app, "nodal")
        TabBuilder.creer_slider(frame_input, "Bubble Point Pressure (psi)", app.pb, 500, 3500, app, "nodal")
        TabBuilder.creer_slider(frame_input, "Water Cut", app.wc, 0.0, 0.95, app, "nodal")
        TabBuilder.creer_slider(frame_input, "Wellhead Pressure P_wh (psi)", app.p_wh, 100, 800, app, "nodal")
        
        ctk.CTkLabel(frame_input, text="COUPLED ARTIFICIAL LIFT", font=("Arial", 12, "bold")).pack(pady=10)
        TabBuilder.creer_slider(frame_input, "ESP Frequency (Hz)", app.esp_freq, 0, 65, app, "nodal")
        TabBuilder.creer_slider(frame_input, "ESP Position (ft above bottom)", app.esp_depth, 0, 5000, app, "nodal")
        TabBuilder.creer_slider(frame_input, "Gas Lift Rate (MMscf/d)", app.gl_rate, 0, 5, app, "nodal")
        TabBuilder.creer_slider(frame_input, "Gas Lift Injection Depth (ft above bottom)", app.gl_depth, 0, 5000, app, "nodal")

        ctk.CTkButton(frame_input, text="Calculate Nodal Solution", command=app.executer_nodal, fg_color="#2ecc71").pack(pady=15, fill="x", padx=10)

    @staticmethod
    def build_pipe_tab(tab, app):
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        frame_input = ctk.CTkFrame(tab, width=340)
        frame_input.grid(row=0, column=0, padx=10, pady=10, sticky="nsw")
        
        ctk.CTkLabel(frame_input, text="SURFACE NETWORK", font=("Arial", 12, "bold")).pack(pady=5)
        TabBuilder.creer_slider(frame_input, "Initial Pressure (psi)", app.p_depart, 200, 1500, app, "surface")
        TabBuilder.creer_slider(frame_input, "Throughput Rate (stb/d)", app.debit_pipe, 500, 6000, app, "surface")
        TabBuilder.creer_slider(frame_input, "Pipeline Length (miles)", app.longueur, 1, 30, app, "surface")
        TabBuilder.creer_slider(frame_input, "Pipe Diameter (in)", app.diam_pipe, 2, 10, app, "surface")
        TabBuilder.creer_slider(frame_input, "Topographic Elevation Change (ft)", app.amplitude_relief, -500, 1500, app, "surface")

        ctk.CTkButton(frame_input, text="Simulate Surface Profile", command=app.executer_pipeline, fg_color="#e67e22").pack(pady=15, fill="x", padx=20)

    @staticmethod
    def creer_slider(master, label, variable, v_min, v_max, app, type_calcul):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=4)
        lbl = ctk.CTkLabel(frame, text=f"{label} : {variable.get():.1f}", font=("Arial", 11))
        lbl.pack(anchor="w")
        
        def command_update(v):
            variable.set(float(v))
            lbl.configure(text=f"{label} : {float(v):.1f}")
            
        s = ctk.CTkSlider(frame, from_=v_min, to=v_max, variable=variable, command=command_update)
        s.pack(fill="x")

        def rafraichir_auto(*args):
            try:
                if type_calcul == "nodal": app.executer_nodal()
                elif type_calcul == "surface": app.executer_pipeline()
            except: pass
        variable.trace_add("write", rafraichir_auto)
