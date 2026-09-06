import numpy as np

class FluidPVTStanding:
    """Calculs Black Oil selon les corrélations rigoureuses de Standing et Beggs-Robinson."""
    def __init__(self, api=35.0, gas_grav=0.65, water_grav=1.07):
        self.api = api
        self.gamma_o = 141.5 / (131.5 + api)
        self.gamma_g = gas_grav
        self.gamma_w = water_grav

    def calculer_proprietes(self, p, t_rankine, gor_base, pb, wc_frac):
        p = max(14.7, p)
        t_f = t_rankine - 459.67
        
        if p >= pb:
            rs = gor_base
        else:
            val = (p / 18.2 + 1.4) * (10**(0.0125 * self.api - 0.00091 * t_f))
            rs = min(gor_base, self.gamma_g * (max(0.0, val))**1.2048)
        
        f = rs * (self.gamma_g / self.gamma_o)**0.5 + 1.25 * t_f
        bo = 0.972 + 0.000147 * (f**1.175)
        bg = 0.02829 * t_rankine / p  
        
        rho_o = (62.4 * self.gamma_o + 0.0136 * rs * self.gamma_g) / bo
        rho_g = 2.7 * self.gamma_g * p / t_rankine
        rho_w = 62.4 * self.gamma_w
        rho_l = (wc_frac * rho_w) + ((1.0 - wc_frac) * rho_o)
        
        mu_dead = 10**(10**(1.8653 - 0.02508 * self.api) * (t_f**-1.157)) - 1.0
        mu_dead = max(0.01, mu_dead)
        a = 10.715 * (rs + 100)**(-0.515)
        b = 5.44 * (rs + 150)**(-0.338)
        mu_o = a * (mu_dead**b)
        
        mu_g = 0.0001 * (9.4 + 0.02 * self.gamma_g) * (t_rankine**1.5) / (209 + 19 * self.gamma_g + t_rankine)
        mu_l = (wc_frac * 1.0) + ((1.0 - wc_frac) * mu_o)
        
        return rho_l, rho_g, mu_l, mu_g, bo, bg, rs


class MultiphaseHydroEngine:
    """Moteur hydraulique implémentant la corrélation industrielle complète de Beggs & Brill (1973)."""
    def __init__(self, rugosite=0.0006):
        self.epsilon = rugosite

    def evaluer_gradient(self, p, t_rankine, q_l_std, gor_local, pb, wc_frac, d_in, pvt, sin_theta=1.0):
        d_ft = d_in / 12.0
        area = (np.pi * d_ft**2) / 4.0
        
        rho_l, rho_g, mu_l, mu_g, bo, bg, rs = pvt.calculer_proprietes(p, t_rankine, gor_local, pb, wc_frac)
        
        q_o_std = q_l_std * (1.0 - wc_frac) / 86400.0
        q_w_std = q_l_std * wc_frac / 86400.0
        q_g_total_std = (q_l_std * gor_local) / 86400.0
        
        q_g_free_std = max(0.0, q_g_total_std - q_o_std * rs)
        q_l_insitu = (q_o_std * bo + q_w_std) * 5.615
        q_g_insitu = q_g_free_std * bg
        
        v_sl = q_l_insitu / area
        v_sg = q_g_insitu / area
        v_m = v_sl + v_sg
        
        if v_m <= 0:
            return (rho_l * sin_theta) / 144.0, rho_l

        # 1. Calcul du Taux de Faux Gaz Amont (Input Liquid Content Lambda_L)
        lambda_l = v_sl / v_m
        
        # 2. Nombre de Froude du mélange (Fr)
        fr = (v_m**2) / (32.2 * d_ft)
        
        # 3. Limites de transition des régimes (Beggs & Brill)
        l1 = 316.0 * (lambda_l**0.302)
        l2 = 0.000925 * (lambda_l**-2.477)
        l3 = 0.10 * (lambda_l**-1.451)
        l4 = 0.5 * (lambda_l**-6.738)
        
        # 4. Identification stricte du Régime d'écoulement
        regime = 0  # 0: Segregated, 1: Intermittent, 2: Distributed, 3: Transition
        hl_0 = 0.0
        
        if (lambda_l < 0.01 and fr < l1) or (lambda_l >= 0.01 and fr < l2):
            regime = 0  # Segregated
            hl_0 = 0.98 * (lambda_l**0.4846) / (fr**0.0868)
        elif (0.01 <= lambda_l < 0.4 and l3 <= fr <= l1) or (lambda_l >= 0.4 and l3 <= fr <= l4):
            regime = 1  # Intermittent
            hl_0 = 0.845 * (lambda_l**0.5351) / (fr**0.0173)
        elif (lambda_l < 0.4 and fr >= l1) or (lambda_l >= 0.4 and fr > l4):
            regime = 2  # Distributed
            hl_0 = 1.065 * (lambda_l**0.5824) / (fr**0.0609)
        elif (0.01 <= lambda_l < 0.4 and l2 <= fr <= l3):
            regime = 3  # Transition
            hl_seg = 0.98 * (lambda_l**0.4846) / (fr**0.0868)
            hl_int = 0.845 * (lambda_l**0.5351) / (fr**0.0173)
            b = (l3 - fr) / (l3 - l2)
            hl_0 = b * hl_seg + (1.0 - b) * hl_int

        hl_0 = max(lambda_l, min(1.0, hl_0))
        
        # 5. Correction d'inclinaison de Beggs & Brill (Hold-up incliné)
        angle_rad = np.arcsin(sin_theta)
        nv = v_m * ((rho_l / max(0.1, 32.2 * 30.0))**0.25)  # 30.0 dynes/cm standard surface tension
        
        if sin_theta >= 0: # Écoulement ascendant (Upfill)
            c = (1.0 - lambda_l) * np.log(max(1e-5, 0.011 * (nv**3.539) / (lambda_l**3.758) / (fr**0.161)))
        else: # Écoulement descendant (Downhill)
            c = (1.0 - lambda_l) * np.log(max(1e-5, 4.7 * (nv**0.124) / (lambda_l**0.369) / (fr**0.091)))
            
        c = max(0.0, c)
        psi = 1.0 + c * (np.sin(1.8 * angle_rad) - 0.333 * (np.sin(1.8 * angle_rad)**3))
        hl = max(lambda_l, min(1.0, hl_0 * psi))
        
        # 6. Propriétés de mélange et calcul du frottement biphasique
        rho_mix = (hl * rho_l) + ((1.0 - hl) * rho_g)
        mu_no_slip = (lambda_l * mu_l) + ((1.0 - lambda_l) * mu_g)
        rho_no_slip = (lambda_l * rho_l) + ((1.0 - lambda_l) * rho_g)
        
        re_ns = max(100, (rho_no_slip * v_m * d_ft) / (mu_no_slip * 0.00067197))
        f_ns = 1.0 / ((-2.0 * np.log10((self.epsilon/d_ft)/3.7 + 2.51/np.sqrt(re_ns)))**2) if re_ns > 2100 else 64.0/re_ns
        
        # Facteur de correction de frottement de Beggs & Brill
        y = max(1e-4, lambda_l / (hl**2))
        if 1.0 < y < 1.2:
            s = np.log(2.2 * y - 1.2)
        else:
            s = np.log(y) / (2.52 - 0.478 * np.log(y))
        f_tp = f_ns * np.exp(s)
        
        grad_grav = (rho_mix * sin_theta) / 144.0
        grad_fric = (f_tp * rho_no_slip * (v_m**2)) / (2.0 * 32.2 * d_ft * 144.0)
        
        return grad_grav + grad_fric, rho_l


class ESPLiftSystem:
    """Courbe synthétique éducative de performance d'ESP."""
    def __init__(self, stages=80):
        self.stages = stages
        self.q_catalog = np.array([0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0])
        self.head_catalog = np.array([50.0, 48.0, 44.0, 38.0, 29.0, 16.0, 2.0])
        self.eff_catalog = np.array([0.0, 30.0, 55.0, 66.0, 62.0, 40.0, 0.0])

    def evaluer_boost(self, q_l_cfs, frequence, rho_l):
        if frequence < 30 or q_l_cfs <= 0: 
            return 0.0, 0.0
        q_gpm = q_l_cfs * 448.8311
        f_ratio = frequence / 60.0
        q_ref = q_gpm / f_ratio
        head_ref = np.interp(q_ref, self.q_catalog, self.head_catalog)
        eff = np.interp(q_ref, self.q_catalog, self.eff_catalog)
        head_reel = head_ref * self.stages * (f_ratio**2)
        dp_psi = (head_reel * rho_l) / 144.0
        return dp_psi, head_reel


class ReservoirIPR:
    """Modélisation d'afflux composite avec inversion de Vogel analytique."""
    @staticmethod
    def calculer_pwf(q, pr, ip, pb):
        q_max_vogel = ip * pb / 1.8
        if pr >= pb:
            q_b = ip * (pr - pb)
            if q <= q_b:
                return pr - (q / ip)
            else:
                ratio = (q - q_b) / max(1.0, q_max_vogel)
                if ratio >= 1.0: 
                    return 0.0
                radical = 0.04 + 3.2 * (1.0 - ratio)
                return pb * ((-0.2 + np.sqrt(max(0.0, radical))) / 1.6)
        else:
            q_max = ip * pr / 1.8
            ratio = q / max(1.0, q_max)
            if ratio >= 1.0: 
                return 0.0
            radical = 0.04 + 3.2 * (1.0 - ratio)
            return pr * ((-0.2 + np.sqrt(max(0.0, radical))) / 1.6)
