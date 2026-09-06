import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# IMPORTATIONS DIRECTES DEPUIS LES COMPOSANTS DU BUREAU
from physics import FluidPVTStanding, MultiphaseHydroEngine, ESPLiftSystem, ReservoirIPR
from solver import ProductionSolver
from gui_tabs import TabBuilder
from reports import ReportGenerator

matplotlib.use("TkAgg")
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PROSIMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PRO-SIM v5.2 — Advanced Beggs & Brill & Ramey Simulator")
        self.geometry("1350x940")

        # Variables Couplées Tkinter (DoubleVar)
        self.pr = ctk.DoubleVar(value=4000.0)
        self.ip = ctk.DoubleVar(value=1.5)
        self.pb = ctk.DoubleVar(value=2500.0)
        self.wc = ctk.DoubleVar(value=0.1)
        self.p_wh = ctk.DoubleVar(value=250.0)
        self.gor_base = ctk.DoubleVar(value=300.0)
        self.depth = ctk.DoubleVar(value=6000.0)
        
        self.esp_freq = ctk.DoubleVar(value=0.0)
        self.esp_depth = ctk.DoubleVar(value=2000.0)
        self.gl_rate = ctk.DoubleVar(value=0.0)       
        self.gl_depth = ctk.DoubleVar(value=3000.0) 

        self.p_depart = ctk.DoubleVar(value=600.0)
        self.debit_pipe = ctk.DoubleVar(value=2000.0)
        self.longueur = ctk.DoubleVar(value=8.0)
        self.diam_pipe = ctk.DoubleVar(value=4.0)
        self.amplitude_relief = ctk.DoubleVar(value=400.0) 

        # Initialisation du moteur résolveur couplé
        self.pvt = FluidPVTStanding()
        self.hydro = MultiphaseHydroEngine()
        self.esp = ESPLiftSystem()
        self.solver = ProductionSolver(self.pvt, self.hydro, self.esp, ReservoirIPR)

        # Onglets principaux
        self.tab_view = ctk.CTkTabview(self, segmented_button_selected_color="#3498db")
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_puits = self.tab_view.add("1. Nodal Analysis (Well)")
        self.tab_pipe = self.tab_view.add("2. Surface Network (Pipeline)")
        self.tab_val = self.tab_view.add("3. Specifications & Formulations v5.2")

        self.configurer_panneaux_interface()

    def configurer_panneaux_interface(self):
        TabBuilder.build_puits_tab(self.tab_puits, self)
        TabBuilder.build_pipe_tab(self.tab_pipe, self)

        # Graphique Puits
        self.frame_graph_puits = ctk.CTkFrame(self.tab_puits)
        self.frame_graph_puits.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.fig_puits, self.ax_puits = plt.subplots(figsize=(6, 5))
        self.canvas_puits = FigureCanvasTkAgg(self.fig_puits, master=self.frame_graph_puits)
        self.canvas_puits.get_tk_widget().pack(fill="both", expand=True)

        # Graphique Pipeline
        self.frame_graph_pipe = ctk.CTkFrame(self.tab_pipe)
        self.frame_graph_pipe.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.fig_pipe, self.ax_pipe = plt.subplots(figsize=(6, 5))
        self.canvas_pipe = FigureCanvasTkAgg(self.fig_pipe, master=self.frame_graph_pipe)
        self.canvas_pipe.get_tk_widget().pack(fill="both", expand=True)

        # Rapport Technique
        self.tab_val.grid_columnconfigure(0, weight=1)
        self.txt_analyse = ctk.CTkTextbox(self.tab_val, font=("Courier New", 12))
        self.txt_analyse.pack(fill="both", expand=True, padx=15, pady=10)
        self.txt_analyse.insert("1.0", ReportGenerator.obtenir_rapport_limites())

    def executer_nodal(self):
        self.ax_puits.clear()
        self.ax_puits.tick_params(colors="white")
        debits_test = list(range(10, 4200, 100))
        
        q_ipr, p_ipr = [], []
        for q in debits_test:
            p_wf = self.solver.ipr.calculer_pwf(q, self.pr.get(), self.ip.get(), self.pb.get())
            if p_wf >= 0:
                q_ipr.append(q)
                p_ipr.append(p_wf)
                
        q_vlp, p_vlp = [], []
        for q in q_ipr:
            p_fond = self.solver.calculer_profil_puits(
                q, self.p_wh.get(), self.depth.get(), self.gor_base.get(),
                self.gl_rate.get(), self.gl_depth.get(), self.esp_freq.get(),
                self.esp_depth.get(), self.pb.get(), self.wc.get()
            )
            if p_fond < self.pr.get() * 1.5:
                q_vlp.append(q)
                p_vlp.append(p_fond)

        q_op, p_op = self.solver.resoudre_point_nodal(
            self.pr.get(), self.ip.get(), self.pb.get(), self.wc.get(), self.p_wh.get(),
            self.depth.get(), self.gor_base.get(), self.gl_rate.get(), self.gl_depth.get(),
            self.esp_freq.get(), self.esp_depth.get()
        )

        self.ax_puits.plot(q_ipr, p_ipr, color="#2ecc71", lw=2.5, label="Analytical IPR (Vogel / Linear)")
        if q_vlp:
            self.ax_puits.plot(q_vlp, p_vlp, color="#e74c3c", lw=2.5, label="VLP — Beggs & Brill + Ramey")
            
        if q_op is not None and q_op > 0:
            self.ax_puits.plot(
                q_op, p_op, 'o', color="#f1c40f", markersize=10,
                markeredgecolor="white", markeredgewidth=1.2,
                label="Operating Point"
            )

            # Callout fixe dans une zone libre du graphique : le texte ne se
            # superpose plus à l'IPR/VLP lorsque le point d'opération se déplace.
            self.ax_puits.text(
                0.03, 0.06,
                f"OPERATING POINT\nQop = {q_op:.0f} stb/d\nPwf = {p_op:.0f} psi",
                transform=self.ax_puits.transAxes,
                ha="left", va="bottom",
                fontsize=10, fontweight="bold", color="white",
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor="#2c3e50", edgecolor="#f1c40f",
                    linewidth=1.5, alpha=0.95
                )
            )

        self.ax_puits.set_title("Coupled P-T Nodal Analysis (Beggs & Brill)", color="white", fontsize=11, fontweight="bold")
        self.ax_puits.set_xlabel("Standard Liquid Rate (stb/day)", color="white")
        self.ax_puits.set_ylabel("Bottomhole Pressure Pwf (psi)", color="white")
        self.ax_puits.grid(True, linestyle="--", alpha=0.3)
        self.ax_puits.set_facecolor("#151515")
        self.fig_puits.patch.set_facecolor("#151515")
        self.ax_puits.legend(facecolor="#2c3e50", edgecolor="none", labelcolor="white")
        self.canvas_puits.draw()

    def executer_pipeline(self):
        self.ax_pipe.clear()
        self.ax_pipe.tick_params(colors="white")
        dist_x, press_y = self.solver.simuler_profil_surface(
            self.p_depart.get(), self.debit_pipe.get(), self.longueur.get(),
            self.diam_pipe.get(), self.amplitude_relief.get(), self.gor_base.get(),
            self.pb.get(), self.wc.get()
        )
        
        self.ax_pipe.plot(dist_x, press_y, color="#3498db", lw=2.5, label="Beggs & Brill Pressure Profile")
        self.ax_pipe.set_title(f"Discrete Hydraulic Profile (Elevation Change: {self.amplitude_relief.get()} ft)", color="white", fontsize=11, fontweight="bold")
        self.ax_pipe.set_xlabel("Pipeline Distance (miles)", color="white")
        self.ax_pipe.set_ylabel("Pipeline Internal Pressure (psi)", color="white")
        self.ax_pipe.grid(True, linestyle="--", alpha=0.3)
        self.ax_pipe.set_facecolor("#151515")
        self.fig_pipe.patch.set_facecolor("#151515")
        self.canvas_pipe.draw()

if __name__ == "__main__":
    app = PROSIMApp()
    app.mainloop()


