import random
import math
from datetime import datetime

class IrrigationSimulation:
    def __init__(self):
        """
        Initialize with a time-scaling approach so that:
          - 1 Martian sol (24.65 hours) completes in 20 real minutes.
        """
        self.real_start_time = datetime.now()

        # 1 sol = ~24.65 hours => 24.65 * 3600 = 88740 simulated seconds
        # 20 real minutes = 1200 real seconds
        # => scale factor ~ 88740 / 1200 = 74.0
        self.simulation_speed_factor = 88740.0 / 1200.0

        # Track dynamic soil moisture
        self.current_soil_moisture = 500  # Starting mid-range
        self.last_update_time = datetime.now()

    def _elapsed_real_seconds(self):
        """
        Returns real-world seconds since the last update,
        which we can use to increment soil moisture, etc.
        """
        now = datetime.now()
        delta = now - self.last_update_time
        self.last_update_time = now
        return delta.total_seconds()

    def _time_of_day_factor(self):
        """
        Computes the 'hour of day' on Mars, scaled so that
        one sol completes in 20 minutes of real time.
        """
        now = datetime.now()
        real_elapsed_seconds = (now - self.real_start_time).total_seconds()
        sim_elapsed_seconds  = real_elapsed_seconds * self.simulation_speed_factor

        # Convert to Martian hours, mod 24.65 so it wraps every sol
        hour_of_sol = (sim_elapsed_seconds / 3600.0) % 24.65
        return hour_of_sol

    def simulate_temperature(self):
        """
        Temperature range for a greenhouse on Mars:
        Let's assume ~0–40 °C daily swing, with a typical center ~20 °C.
        Use a sine wave + random noise.
        """
        hour = self._time_of_day_factor()

        # Example: base ~20, amplitude ~20 => 0-40 range
        BASE_TEMPERATURE = 20
        AMP_TEMPERATURE = 20
        temperature = BASE_TEMPERATURE + AMP_TEMPERATURE * math.sin((2 * math.pi / 24.65) * (hour - 6))
        # Random fluctuation
        temperature += random.uniform(-2, 2)
        # Clip just in case
        temperature = max(0, min(50, temperature))
        return int(temperature)

    def simulate_humidity(self):
        """
        Humidity in a controlled greenhouse might be 30–80%.
        We use a cosine wave for daily variation + random noise.
        """
        hour = self._time_of_day_factor()
        BASE_HUMIDITY = 50
        AMP_HUMIDITY = 40  # so it oscillates ~40 above/below base
        humidity = BASE_HUMIDITY + AMP_HUMIDITY * math.cos((2 * math.pi / 24.65) * (hour - 6))
        humidity += random.uniform(-5, 5)
        # Clip 0–100
        humidity = max(0, min(100, humidity))
        return int(humidity)

    def simulate_pressure(self):
        """
        Assume a pressurized greenhouse ~900–1100 hPa range (converted to some internal units)
        or a typical irrigation line pressure if you prefer. We'll do 50–160 as an irrigation range.
        """
        hour = self._time_of_day_factor()
        BASE_PRESSURE = 100    # center point
        AMP_PRESSURE = 40      # ±30
        pressure = BASE_PRESSURE + AMP_PRESSURE * math.sin((2 * math.pi / 24.65) * hour)
        pressure += random.uniform(-5, 5)
        # Clip to 50–160
        pressure = max(40, min(160, pressure))
        return int(pressure)

    def simulate_soil_moisture(self, pump_on: bool, valve_open: bool):
        """
        Soil moisture in [0..1000].
        If pump & valve are both on, it increases; otherwise it decreases slowly.
        """
        elapsed_real = self._elapsed_real_seconds()

        # Evaporation vs. irrigation rates
        # These might be bigger if we want to see faster changes
        evaporation_rate = 0.03
        irrigation_rate = 0.1

        moisture_change = -evaporation_rate * elapsed_real
        if pump_on and valve_open:
            moisture_change += irrigation_rate * elapsed_real

        self.current_soil_moisture += moisture_change
        self.current_soil_moisture = max(0, min(1000, self.current_soil_moisture))
        return int(self.current_soil_moisture)

    def simulate_water_flow(self, pump_on: bool, valve_open: bool):
        """
        If pump+valve are on, flow ~400–600. Otherwise near zero.
        """
        if pump_on and valve_open:
            flow_value = 500 + random.uniform(-100, 100)
        else:
            flow_value = random.uniform(0, 5)
        return int(max(0, min(1000, flow_value)))

    def update_sensors(self, pump_on: bool, valve_open: bool):
        """
        Return all sensor readings as a tuple:
          SoilMoisture, Temperature, Humidity, WaterFlow, Pressure
        """
        soil_moisture = self.simulate_soil_moisture(pump_on, valve_open)
        temperature   = self.simulate_temperature()
        humidity      = self.simulate_humidity()
        water_flow    = self.simulate_water_flow(pump_on, valve_open)
        pressure      = self.simulate_pressure()

        return (soil_moisture, temperature, humidity, water_flow, pressure)
