import pandas as pd
from pathlib import Path

import fastsim as fsim
import argparse
# import fsim.Cycle as Cycle
# from fastsim.vehicles import Vehicle
# from fastsim.simdrive import SimDrive


parser = argparse.ArgumentParser()
parser.add_argument(
    "--cycle", "-c",
    type=str,
    default="hwfet.csv",
    choices=["udds.csv", "hwfet.csv", "us06.csv"],
    help="Cycle to use for the simulation. Default is 'hwfet.csv'."
    )
args = parser.parse_args()

# -----------------------------
# 1) Build a Kenworth T680E–like BEV
# -----------------------------

veh = fsim.Vehicle.from_file("/home/zacmaughan/repos/routee-powertrain/scripts/fastsim/kenworth_t680e.yaml")

# -----------------------------
# 2) Build a “classic U.S.” cycle (UDDS, HWFET, US06)
# -----------------------------
# The UDDS is a typical urban cycle, HWFET is a highway cycle, and US06 is an aggressive highway cycle.

cycle = fsim.Cycle.from_file(args.cycle)

# -----------------------------
# 3) Run the simulation
# -----------------------------
sd = fsim.SimDrive(cycle, veh)
# For BEVs, you can provide an initial SOC; FASTSim will iterate to hit end-of-cycle SOC if needed.
out = sd.sim_drive(init_soc=0.8)

# -----------------------------
# 4) Summarize and export results
# -----------------------------
# The SimDrive object holds achieved speed, power flows, battery SOC, distance, etc.
# Field names can vary across FASTSim versions; the most stable items are in sd.cyc (the cycle) and
# battery SOC arrays. If a key below is missing in your version, comment it out and re-run.

summary = {
    "vehicle": veh.name,
    "route_name": "Classic U.S. Cycle",
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