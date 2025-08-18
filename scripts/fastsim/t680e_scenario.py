import pandas as pd
from pathlib import Path

import fastsim as fsim
from fastsim.cycle import Cycle
from fastsim.vehicle import Vehicle
from fastsim.simdrive import SimDrive

# -----------------------------
# 1) Build a Kenworth T680E–like BEV
# -----------------------------
# SOURCES (specs):
# - The T680E is a Class 8 battery-electric day cab. Public materials describe a 396 kWh pack (nominal/usable varies by doc),
#   approx ~150-250 mi range depending on duty, and ~536 hp (~400 kW) traction (varies by configuration).
#   See Kenworth spec pages & press releases. :contentReference[oaicite:0]{index=0}
#
# NOTE: FASTSim expects a fairly detailed vehicle dict. Below are reasonable, documented fields with snake_case
# names per the FASTSim Python API. You can adjust as you calibrate.
# API reference for Vehicle.from_dict / Cycle.from_file / SimDrive.sim_drive: :contentReference[oaicite:1]{index=1}

t680e = {
    # --- identity ---
    "veh_name": "Kenworth T680E",
    "veh_pt_type": "BEV",  # Battery Electric Vehicle

    # --- massing ---
    # Tractor day cab curb ~ 8–10t; with chassis & e-components often >10t; add payload for Class 8. We start with a moderate GC mass.
    # Adjust to your use case & validation data.
    "glider_kg": 10500.0,            # chassis/body without powertrain (inferred)
    "mc_mass_kg": 450.0,             # traction motor + inverter mass (inferred)
    "ess_mass_kg": 2500.0,           # 396 kWh Li-ion pack ~ 6–7 kg/kWh typical HD pack incl. structure (inferred)
    "cargo_kg": 8000.0,              # payload for day-cab line-haul short route (example)
    "fs_mass_kg": 0.0,               # no fuel system
    "comp_mass_kg": 300.0,           # auxiliaries (HVAC pumps, etc., inferred)
    "veh_override_kg": -1.0,         # let FASTSim compute from components

    # --- road load ---
    "drag_coef": 0.6,                # Class 8 aero, day cab; tune if you have a C_d·A (inferred)
    "frontal_area_m2": 10.0,         # tractor FA (inferred)
    "rr_coeff": 0.0065,              # heavy truck tire rolling resistance (inferred typical)
    "wheel_rr_radius_m": 0.5,        # effective wheel radius ~ 19.5–22.5" tires (inferred)

    # --- driveline / gearing ---
    "mc_max_kw": 400.0,              # ~536 hp peak ≈ 400 kW (spec-ish; some materials list similar) :contentReference[oaicite:2]{index=2}
    "mc_peak_efficiency": 0.95,      # modern e-axle peak efficiency (typical)
    "mc_kwh_per_kg": 0.0,            # leave 0 for not using mass-derived calc
    "mc_full_eff_array": [],         # empty -> FASTSim default map
    "mc_eff_type": 1,                # default eff curve family (let FASTSim choose built-in)
    "fd_efficiency": 0.97,           # final drive efficiency (typical)
    "fd_ratio": 3.5,                 # overall reduction (example—tune)
    "max_trq_nm": 3500.0,            # generous HD e-axle torque (inferred)
    "idle_kw": 2.5,                  # parasitic at idle (example)

    # --- battery / charging ---
    "ess_max_kwh": 396.0,            # pack energy (spec figure commonly cited for T680E) :contentReference[oaicite:3]{index=3}
    "ess_max_kw": 400.0,             # discharge power ~= motor peak (constrained by thermal)
    "ess_min_soc": 0.1,              # reserve
    "ess_max_soc": 0.9,              # preserve pack life in sim
    "ess_round_trip_efficiency": 0.93, # typical Li-ion round trip
    "ess_chg_efficiency": 0.95,

    # --- auxiliaries / HVAC ---
    "aux_kw": 2.0,                   # hotel loads, compressors, etc. (example)
    "trans_efficiency": 1.0,         # single-speed e-axle -> no separate trans losses

    # --- limits/others (defaults generally OK) ---
    "max_accel_m_per_s2": 1.0,       # governs trace following if underpowered (example)
    "regen_brake_mode": 1,           # allow regen
}

veh = Vehicle.from_dict(t680e)

# -----------------------------
# 2) Build a “classic U.S.” mixed cycle (UDDS + HWFET + US06)
# -----------------------------
# FASTSim ships standard EPA cycles in fastsim/resources/cycles; Cycle.from_file finds them by name.
# (e.g., "udds", "hwfet", "us06"). API docs: :contentReference[oaicite:4]{index=4}

udds = Cycle.from_file("udds")
hwfet = Cycle.from_file("hwfet")
us06 = Cycle.from_file("us06")

# Concatenate (urban → highway → aggressive highway)
from fastsim.cycle import concat as cyc_concat
mixed = cyc_concat([udds, hwfet, us06])

# -----------------------------
# 3) Run the simulation
# -----------------------------
sd = SimDrive(mixed, veh)
# For BEVs, you can provide an initial SOC; FASTSim will iterate to hit end-of-cycle SOC if needed.
out = sd.sim_drive(init_soc=0.8)

# -----------------------------
# 4) Summarize and export results
# -----------------------------
# The SimDrive object holds achieved speed, power flows, battery SOC, distance, etc.
# Field names can vary across FASTSim versions; the most stable items are in sd.cyc (the cycle) and
# battery SOC arrays. If a key below is missing in your version, comment it out and re-run.

summary = {
    "vehicle": veh.veh_name,
    "route_name": "UDDS+HWFET+US06",
    "total_distance_km": getattr(sd, "dist_m", 0.0) / 1000.0 if hasattr(sd, "dist_m") else None,
    "final_soc": getattr(sd, "ess_soc", [None])[-1] if hasattr(sd, "ess_soc") else None,
}

print("=== FASTSim summary ===")
for k, v in summary.items():
    print(f"{k}: {v}")

# Build a per-step dataframe useful for RouteE
# (RouteE typically wants per-link energy or per-second energy you can aggregate to links.)
time_s = getattr(sd.cyc, "time_s", None)
mps = getattr(sd, "ach_mps", None) if hasattr(sd, "ach_mps") else getattr(sd.cyc, "mps", None)
soc = getattr(sd, "ess_soc", None)
battery_kw = getattr(sd, "ess_kw_out_ach", None) if hasattr(sd, "ess_kw_out_ach") else None
dist_step_m = None
if hasattr(sd.cyc, "trapz_step_distances"):
    # distance covered per step (if available in your version)
    dist_step_m = sd.cyc.trapz_step_distances()

df = pd.DataFrame({
    "time_s": time_s if time_s is not None else [],
    "speed_mps": mps if mps is not None else [],
    "soc": soc if soc is not None else [],
    "battery_kw": battery_kw if battery_kw is not None else [],
    "step_distance_m": dist_step_m if dist_step_m is not None else [],
})

out_path = Path("t680e_mixed_route_results.csv")
df.to_csv(out_path, index=False)
print(f"\nWrote {out_path.resolve()}")