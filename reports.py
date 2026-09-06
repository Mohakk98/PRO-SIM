class ReportGenerator:
    """Physical Model Transparency Report Generator pour PRO-SIM v5.2."""
    @staticmethod
    def obtenir_rapport_limites():
        return (
            "=========================================================================\n"
            "   PRO-SIM v5.2: ADVANCED MULTIPHASE & THERMAL COUPLING SIMULATOR\n"
            "=========================================================================\n\n"
            "1. BEGGS & BRILL (1973) CORRELATION IMPLEMENTATION\n"
            "   - The hydraulic engine determines the local Flow Regime at each step:\n"
            "     Segregated, Intermittent, Distributed, or Transition (Froude vs Lambda_L).\n"
            "   - Inclined liquid Hold-up calculated using the slope correction factor C.\n"
            "   - Beggs & Brill two-phase friction referenced to the local No-Slip friction.\n\n"
            "2. NONLINEAR THERMAL COUPLING (RAMEY / AL-RAMEZI MODEL)\n"
            "   - Isothermal approximation removed. Iterative solution of energy loss.\n"
            "   - Calcul du profil de température non linéaire en fonction de la profondeur, de la masse\n"
            "     de fluide (Cp) et du transfert thermique global (U) avec la formation géologique.\n\n"
            "3. REAL-TIME INTERACTIVE STABILITY (TRACES)\n"
            "   - Les traceurs d'événements (traces Tkinter) ré-exécutent instantanément la marche en\n"
            "     pression-température Beggs & Brill pour une déformation fluide au mouvement de la souris."
        )
