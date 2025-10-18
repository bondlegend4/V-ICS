PROGRAM ThermalControl
VAR
    (* Inputs from Modbus server *)
    temperature AT %IW100 : INT;        (* Temperature × 100 in Kelvin *)
    heater_feedback AT %IW101 : INT;    (* Heater state: 0=OFF, 100=ON *)
    
    (* Output to Modbus server *)
    heater_command AT %QX0.0 : BOOL;    (* Heater control coil *)
    
    (* Control parameters *)
    setpoint : INT := 29315;             (* 293.15 K = 20°C *)
    hysteresis : INT := 200;             (* ±2°C deadband *)
    
    (* Status variables for monitoring *)
    temp_celsius : REAL;
    temp_kelvin : REAL;
    heater_is_on : BOOL;
END_VAR

(* Convert temperature to human-readable formats *)
temp_kelvin := INT_TO_REAL(temperature) / 100.0;
temp_celsius := temp_kelvin - 273.15;

(* Check heater feedback status *)
heater_is_on := (heater_feedback = 100);

(* Simple bang-bang temperature control *)
IF temperature < (setpoint - hysteresis) THEN
    (* Too cold - turn heater ON *)
    heater_command := TRUE;
ELSIF temperature > (setpoint + hysteresis) THEN
    (* Too hot - turn heater OFF *)
    heater_command := FALSE;
    (* ELSE: maintain current state (within deadband) *)
END_IF;

END_PROGRAM