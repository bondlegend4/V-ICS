PROGRAM irrigation_ST
  VAR
    SoilMoisture AT %IW0.0 : INT;
  END_VAR
  VAR
    SoilMoistureMin : INT := 300;
    SoilMoistureMax : INT := 800;
  END_VAR
  VAR
    Temperature AT %IW0.1 : INT;
  END_VAR
  VAR
    TempMin : INT := 20;
    TempMax : INT := 40;
  END_VAR
  VAR
    Humidity AT %IW0.2 : INT;
  END_VAR
  VAR
    HumidityMin : INT := 50;
    HumidityMin0 : INT := 90;
  END_VAR
  VAR
    WaterFlow AT %IW0.3 : INT;
  END_VAR
  VAR
    FlowMin : INT := 500;
    FlowMax : INT := 1000;
  END_VAR
  VAR
    Pressure AT %IW0.4 : INT;
  END_VAR
  VAR
    PressureMin : INT := 50;
    PressureMax : INT := 150;
  END_VAR
  VAR
    PumpControl AT %QX0.0 : BOOL;
    ValveControl AT %QX0.1 : BOOL;
  END_VAR

  IF (SoilMoisture < SoilMoistureMax) THEN
      IF (Temperature > TempMin) AND (Temperature < TempMax) THEN
          IF (Pressure > PressureMin) AND (Pressure < PressureMax) THEN
              IF (WaterFlow > FlowMin) AND (WaterFlow < FlowMax) THEN
                  PumpControl := TRUE;
                  ValveControl := TRUE;
              ELSE
                  PumpControl := FALSE;
                  ValveControl := FALSE;
              END_IF;
          ELSE
              PumpControl := FALSE;
              ValveControl := FALSE;
          END_IF;
      ELSE
          PumpControl := FALSE;
          ValveControl := FALSE;
      END_IF;
  ELSE
      PumpControl := FALSE;
      ValveControl := FALSE;
  END_IF;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : irrigation_ST;
  END_RESOURCE
END_CONFIGURATION

(*DBG:char md5[] = "bf61d6f7e0f1bec1fb8d8ac3d512d365";*)
(*DBG:/**)
(*DBG: * This file is part of OpenPLC Runtime*)
(*DBG: **)
(*DBG: * Copyright (C) 2023 Autonomy, GP Orcullo*)
(*DBG: * Based on the work by GP Orcullo on Beremiz for uC*)
(*DBG: **)
(*DBG: * This program is free software; you can redistribute it and/or*)
(*DBG: * modify it under the terms of the GNU General Public License*)
(*DBG: * as published by the Free Software Foundation; either version 2*)
(*DBG: * of the License, or (at your option) any later version.*)
(*DBG: **)
(*DBG: * This program is distributed in the hope that it will be useful,*)
(*DBG: * but WITHOUT ANY WARRANTY; without even the implied warranty of*)
(*DBG: * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the*)
(*DBG: * GNU General Public License for more details.*)
(*DBG: **)
(*DBG: * You should have received a copy of the GNU General Public License*)
(*DBG: * along with this program; If not, see <http://www.gnu.org/licenses/>.*)
(*DBG: **)
(*DBG: */*)
(*DBG:*)
(*DBG:#include <stdbool.h>*)
(*DBG:*)
(*DBG:#include "iec_types_all.h"*)
(*DBG:#include "POUS.h"*)
(*DBG:*)
(*DBG:#define SAME_ENDIANNESS      0*)
(*DBG:#define REVERSE_ENDIANNESS   1*)
(*DBG:*)
(*DBG:uint8_t endianness;*)
(*DBG:*)
(*DBG:*)
(*DBG:extern IRRIGATION_ST RES0__INSTANCE0;*)
(*DBG:*)
(*DBG:static const struct {*)
(*DBG:    void *ptr;*)
(*DBG:    __IEC_types_enum type;*)
(*DBG:} debug_vars[] = {*)
(*DBG:    {&(RES0__INSTANCE0.SOILMOISTURE), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.SOILMOISTUREMIN), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.SOILMOISTUREMAX), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.TEMPERATURE), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.TEMPMIN), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.TEMPMAX), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.HUMIDITY), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.HUMIDITYMIN), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.HUMIDITYMIN0), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.WATERFLOW), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.FLOWMIN), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.FLOWMAX), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.PRESSURE), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.PRESSUREMIN), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.PRESSUREMAX), INT_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.PUMPCONTROL), BOOL_ENUM},*)
(*DBG:    {&(RES0__INSTANCE0.VALVECONTROL), BOOL_ENUM},*)
(*DBG:};*)
(*DBG:*)
(*DBG:#define VAR_COUNT               17*)
(*DBG:*)
(*DBG:uint16_t get_var_count(void)*)
(*DBG:{*)
(*DBG:    return VAR_COUNT;*)
(*DBG:}*)
(*DBG:*)
(*DBG:size_t get_var_size(size_t idx)*)
(*DBG:{*)
(*DBG:    if (idx >= VAR_COUNT)*)
(*DBG:    {*)
(*DBG:        return 0;*)
(*DBG:    }*)
(*DBG:    switch (debug_vars[idx].type) {*)
(*DBG:    case BOOL_ENUM:*)
(*DBG:        return sizeof(BOOL);*)
(*DBG:    case INT_ENUM:*)
(*DBG:        return sizeof(INT);*)
(*DBG:    default:*)
(*DBG:        return 0;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void *get_var_addr(size_t idx)*)
(*DBG:{*)
(*DBG:    void *ptr = debug_vars[idx].ptr;*)
(*DBG:*)
(*DBG:    switch (debug_vars[idx].type) {*)
(*DBG:    case BOOL_ENUM:*)
(*DBG:        return (void *)&((__IEC_BOOL_t *) ptr)->value;*)
(*DBG:    case INT_ENUM:*)
(*DBG:        return (void *)&((__IEC_INT_t *) ptr)->value;*)
(*DBG:    default:*)
(*DBG:        return 0;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void force_var(size_t idx, bool forced, void *val)*)
(*DBG:{*)
(*DBG:    void *ptr = debug_vars[idx].ptr;*)
(*DBG:*)
(*DBG:    if (forced) {*)
(*DBG:        size_t var_size = get_var_size(idx);*)
(*DBG:        switch (debug_vars[idx].type) {*)
(*DBG:        case BOOL_ENUM: {*)
(*DBG:            memcpy(&((__IEC_BOOL_t *) ptr)->value, val, var_size);*)
(*DBG:            //((__IEC_BOOL_t *) ptr)->value = *((BOOL *) val);*)
(*DBG:            ((__IEC_BOOL_t *) ptr)->flags |= __IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:        case INT_ENUM: {*)
(*DBG:            memcpy(&((__IEC_INT_t *) ptr)->value, val, var_size);*)
(*DBG:            //((__IEC_INT_t *) ptr)->value = *((INT *) val);*)
(*DBG:            ((__IEC_INT_t *) ptr)->flags |= __IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:        default:*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:    } else {*)
(*DBG:        switch (debug_vars[idx].type) {*)
(*DBG:        case BOOL_ENUM:*)
(*DBG:            ((__IEC_BOOL_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        case INT_ENUM:*)
(*DBG:            ((__IEC_INT_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;*)
(*DBG:            break;*)
(*DBG:        default:*)
(*DBG:            break;*)
(*DBG:        }*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void swap_bytes(void *ptr, size_t size) *)
(*DBG:{*)
(*DBG:    uint8_t *bytePtr = (uint8_t *)ptr;*)
(*DBG:    size_t i;*)
(*DBG:    for (i = 0; i < size / 2; ++i) *)
(*DBG:    {*)
(*DBG:        uint8_t temp = bytePtr[i];*)
(*DBG:        bytePtr[i] = bytePtr[size - 1 - i];*)
(*DBG:        bytePtr[size - 1 - i] = temp;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void trace_reset(void)*)
(*DBG:{*)
(*DBG:    for (size_t i=0; i < VAR_COUNT; i++) *)
(*DBG:    {*)
(*DBG:        force_var(i, false, 0);*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void set_trace(size_t idx, bool forced, void *val)*)
(*DBG:{*)
(*DBG:    if (idx >= 0 && idx < VAR_COUNT) *)
(*DBG:    {*)
(*DBG:        if (endianness == REVERSE_ENDIANNESS)*)
(*DBG:        {*)
(*DBG:            // Aaaaarghhhh... Stupid AVR is Big Endian.*)
(*DBG:            swap_bytes(val, get_var_size(idx));*)
(*DBG:        }*)
(*DBG:*)
(*DBG:        force_var(idx, forced, val);*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)
(*DBG:void set_endianness(uint8_t value)*)
(*DBG:{*)
(*DBG:    if (value == SAME_ENDIANNESS || value == REVERSE_ENDIANNESS)*)
(*DBG:    {*)
(*DBG:        endianness = value;*)
(*DBG:    }*)
(*DBG:}*)
(*DBG:*)