PROGRAM MinimalTest
VAR
    (* Just read temperature *)
    temperature AT %IW100 : INT;
    
    (* Manual heater control - toggle every 5 seconds *)
    heater_command AT %QX0.0 : BOOL;
    
    (* Timer *)
    counter : INT := 0;
END_VAR

(* Increment counter every scan *)
counter := counter + 1;

(* Toggle heater every ~5000 scans (depends on scan time) *)
IF counter > 5000 THEN
    heater_command := NOT heater_command;
    counter := 0;
END_IF;

END_PROGRAM