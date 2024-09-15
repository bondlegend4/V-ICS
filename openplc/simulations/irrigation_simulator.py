import random

class IrrigationSimulation:
    def simulate_soil_moisture(self):
        return random.randint(300, 800)

    def simulate_temperature(self):
        return random.randint(20, 40)

    def simulate_humidity(self):
        return random.randint(50, 90)

    def simulate_water_flow(self):
        return random.randint(500, 1000)

    def simulate_pressure(self):
        return random.randint(50, 150)
