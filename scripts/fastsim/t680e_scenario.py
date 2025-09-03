import polars as pl
from pathlib import Path

import fastsim as fsim
# -----------------------------
# 1) Build a Kenworth T680E BEV
# -----------------------------

veh = fsim.Vehicle.from_file("/home/zacmaughan/repos/routee-powertrain/scripts/fastsim/kenworth_t680e.yaml")
veh.set_save_interval(1)  # Set save interval to 1 second for detailed history

# -----------------------------
# 2) Build a “classic U.S.” cycle (UDDS, HWFET)
# -----------------------------
# The UDDS is a typical urban cycle, HWFET is a highway cycle

cycle = fsim.Cycle.from_file("/home/zacmaughan/repos/routee-powertrain/scripts/fastsim/hwfet.csv")

# -----------------------------
# 3) Run the simulation
# -----------------------------
sd = fsim.SimDrive(veh, cycle)
sd.walk()  # populates histories

# -----------------------------
# 4) Convert to DataFrame
# -----------------------------
df = sd.to_dataframe()

# ----------------------------------------
# 5) Compute dt, step energy, cumulative energy
# ----------------------------------------
df = df.with_columns([
    (pl.col("cyc.time_seconds").diff().fill_null(0)).alias("dt_s"),
    (pl.col("veh.pt_type.BEV.res.history.pwr_out_electrical_watts") * 
     pl.col("cyc.time_seconds").diff().fill_null(0)).alias("battery_energy_step_j"),
])

df = df.with_columns(
    (pl.col("battery_energy_step_j").cum_sum()).alias("battery_energy_cum_j")
)

df = df.with_columns(
    (pl.col("battery_energy_cum_j") / 3.6e6).alias("battery_energy_cum_kwh")
)

# ----------------------------------------
# 6) Summarize key metrics
# ----------------------------------------
total_distance_km = (
    (df["veh.history.speed_ach_meters_per_second"] * df["dt_s"]).sum() / 1000
)

final_soc = df["veh.pt_type.BEV.res.history.soc"].to_numpy()[-1]
total_energy_kwh = df["battery_energy_cum_kwh"].to_numpy()[-1]

summary = {
    "vehicle": "Kenworth T680E",
    "route_name": "HWFET Cycle",
    "total_distance_km": total_distance_km,
    "final_soc": final_soc,
    "total_energy_kwh": total_energy_kwh,
}

print("=== FASTSim summary ===")
for k, v in summary.items():
    print(f"{k}: {v}")

# ----------------------------------------
# 7) Export CSV for RouteE
# ----------------------------------------
out_path = Path("t680e_hwfet_routee.csv")

df_export = df.select([
    "cyc.time_seconds",
    "veh.history.speed_ach_meters_per_second",
    "veh.pt_type.BEV.res.history.soc",
    "battery_energy_step_j",
    "battery_energy_cum_j",
])

df_export.write_csv(out_path)
print(f"\nWrote RouteE-compatible CSV: {out_path.resolve()}")