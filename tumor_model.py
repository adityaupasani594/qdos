import numpy as np


class GompertzTumorModel:

    def __init__(self, drug_strength=None, drug_toxicity=None, r=0.12, K=1e9):

        self.r = r
        self.K = K

        self.drug_strength = {
            "Drug_A": 0.30,
            "Drug_B": 0.25,
            "Drug_C": 0.35,
        }

        self.drug_toxicity = {
            "Drug_A": 0.6,
            "Drug_B": 0.5,
            "Drug_C": 0.8,
        }

        if drug_strength:
            self.drug_strength.update(drug_strength)

        if drug_toxicity:
            self.drug_toxicity.update(drug_toxicity)

        self.schedule = None


    def set_schedule(self, schedule):

        self.schedule = schedule


    def drug_effect(self, t):

        if not self.schedule:
            return 0.0

        day = int(t)
        total_kill = 0.0

        for drug in self.schedule:
            if day < len(self.schedule[drug]) and self.schedule[drug][day] == 1:
                total_kill += self.drug_strength.get(drug, 0.0)

        return total_kill


    def gompertz_equation(self, N, t):

        growth = self.r * N * np.log(self.K / N)
        kill = self.drug_effect(t) * N

        return growth - kill


    def gompertz_no_treatment(self, N, t):

        return self.r * N * np.log(self.K / N)