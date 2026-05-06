import numpy as np
from scipy.integrate import odeint

from tumor_model import GompertzTumorModel


class TumorSimulator:

    def __init__(self, schedule, initial_tumor_size=1e6, drug_strength=None, drug_toxicity=None, clearance_rate=0.3):

        self.schedule = schedule
        self.model = GompertzTumorModel(
            drug_strength=drug_strength,
            drug_toxicity=drug_toxicity,
        )
        self.model.set_schedule(schedule)
        self.initial_tumor_size = initial_tumor_size
        self.clearance_rate = clearance_rate
        self.simulation_days = len(next(iter(schedule.values()))) if schedule else 0
        self.time = np.linspace(0, self.simulation_days, 200)


    def run_with_treatment(self):

        solution = odeint(
            self.model.gompertz_equation,
            self.initial_tumor_size,
            self.time,
        )

        return solution.flatten()


    def run_without_treatment(self):

        solution = odeint(
            self.model.gompertz_no_treatment,
            self.initial_tumor_size,
            self.time,
        )

        return solution.flatten()


    def calculate_toxicity(self):

        toxicity_curve = []
        total = 0.0

        for day in range(self.simulation_days):
            total *= np.exp(-self.clearance_rate)
            daily = 0.0

            for drug in self.schedule:
                if self.schedule[drug][day] == 1:
                    daily += self.model.drug_toxicity.get(drug, 0.0)

            total += daily
            toxicity_curve.append(total)

        return toxicity_curve


    def calculate_statistics(self, tumor_curve):

        final_size = tumor_curve[-1]
        reduction = (
            (self.initial_tumor_size - final_size) /
            self.initial_tumor_size
        ) * 100

        return final_size, reduction