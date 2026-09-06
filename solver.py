import numpy as np

class ProductionSolver:
    """Solveur avec couplage thermique non linéaire de Ramey et hydraulique Beggs & Brill."""
    def __init__(self, pvt, hydro_engine, esp, ipr_model):
        self.pvt = pvt
        self.hydro = hydro_engine
        self.esp = esp
        self.ipr = ipr_model

    def calculer_profil_puits(self, q, p_wh, depth, gor_base, gl_rate, gl_depth, esp_freq, esp_depth, pb, wc):
        """Intégration couplée Pression-Température descendante (Équation d'énergie non linéaire)."""
        p = p_wh
        dz = 100.0
        n_steps = int(depth / dz)
        
        # Conditions thermiques du puits (Température en tête de puits initiale)
        t_surface_f = 80.0 
        t_geothermique_fond_f = 160.0  # Gradient géothermique du gisement
        gradient_geothermique = (t_geothermique_fond_f - t_surface_f) / depth
        
        # Facteur de relaxation thermique Global d'Al-Ramezi / Ramey (A en pieds)
        # Supposant une capacité calorifique du fluide Cp=0.6 BTU/lb*F et un transfert global U
        u_global = 1.5  # BTU/hr*ft2*F
        cp_fluide = 0.6
        w_debit_masse = (q * 350.0 * 1.06) / 86400.0  # lb/s aproximé
        a_relaxation = (w_debit_masse * cp_fluide * 3600.0) / (max(0.1, np.pi * (2.441/12.0) * u_global))
        
        t_courante_f = t_surface_f
        
        for step in range(n_steps):
            z_courant = step * dz
            
            # 1. Équation de Ramey pour le profil de température non linéaire local
            t_formation = t_surface_f + gradient_geothermique * z_courant
            t_courante_f = t_formation - gradient_geothermique * a_relaxation + (t_surface_f - t_surface_f + gradient_geothermique * a_relaxation) * np.exp(-max(0.0, dz / max(1.0, a_relaxation)))
            t_rankine = t_courante_f + 459.67
            
            # 2. Gestion segmentée du Gas Lift
            z_injection_gl = depth - gl_depth
            if gl_rate > 0 and z_courant < z_injection_gl:
                gor_local = gor_base + (gl_rate * 1e6 / max(1.0, q))
            else:
                gor_local = gor_base
                
            grad, rho_l = self.hydro.evaluer_gradient(p, t_rankine, q, gor_local, pb, wc, 2.441, self.pvt, sin_theta=1.0)
            p += grad * dz
            
            # 3. Injection ponctuelle de la charge ESP
            if esp_freq >= 30 and abs(z_courant - (depth - esp_depth)) < (dz / 2):
                q_cfs = (q * 5.615) / 86400.0
                dp_esp, _ = self.esp.evaluer_boost(q_cfs, esp_freq, rho_l)
                p -= dp_esp
                
        return p

    def simuler_profil_surface(self, p_depart, q, longueur_miles, diam_in, amplitude_relief, gor_base, pb, wc):
        dx_ft = 528.0
        steps = int((longueur_miles * 5280.0) / dx_ft)
        dist_x, press_y = [], []
        p_courante = p_depart
        t_rankine = 520.0  # Température de ligne stable
        
        x_vals = np.linspace(0, longueur_miles * 5280.0, steps + 1)
        z_profile = (amplitude_relief * (x_vals / max(1.0, x_vals[-1]))) + 60.0 * np.sin(4 * np.pi * x_vals / max(1.0, x_vals[-1]))
        
        for i in range(steps):
            dist_x.append(x_vals[i] / 5280.0)
            press_y.append(p_courante)
            
            dz = z_profile[i+1] - z_profile[i]
            local_sin = dz / dx_ft
            
            grad, _ = self.hydro.evaluer_gradient(p_courante, t_rankine, q, gor_base, pb, wc, diam_in, self.pvt, sin_theta=local_sin)
            p_courante -= (grad * dx_ft)
            if p_courante < 14.7: 
                p_courante = 14.7
                
        dist_x.append(x_vals[-1] / 5280.0)
        press_y.append(p_courante)
        return dist_x, press_y

    def resoudre_point_nodal(self, pr, ip, pb, wc, p_wh, depth, gor_base, gl_rate, gl_depth, esp_freq, esp_depth):
        def residu_pression(q_essai):
            if q_essai <= 0: return pr - p_wh
            p_ipr = self.ipr.calculer_pwf(q_essai, pr, ip, pb)
            try:
                p_vlp = self.calculer_profil_puits(q_essai, p_wh, depth, gor_base, gl_rate, gl_depth, esp_freq, esp_depth, pb, wc)
            except:
                p_vlp = pr * 3.0
            return p_ipr - p_vlp

        q_inf, q_sup = None, None
        debits_scan = np.linspace(5.0, 6000.0, 40)
        residus_scan = [residu_pression(q) for q in debits_scan]
        
        for i in range(len(debits_scan) - 1):
            if residus_scan[i] * residus_scan[i+1] <= 0:
                q_inf = debits_scan[i]
                q_sup = debits_scan[i+1]
                break
                
        if q_inf is None:
            return None, None
            
        f_inf = residu_pression(q_inf)
        for _ in range(30):
            q_milieu = 0.5 * (q_inf + q_sup)
            f_milieu = residu_pression(q_milieu)
            if abs(f_milieu) < 0.1: break
            if f_inf * f_milieu < 0:
                q_sup = q_milieu
            else:
                q_inf = q_milieu
                f_inf = f_milieu
                
        q_op = 0.5 * (q_inf + q_sup)
        p_op = self.ipr.calculer_pwf(q_op, pr, ip, pb)
        return q_op, p_op
