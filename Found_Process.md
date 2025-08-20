# The Current Process of How to work RouteE
## What I have Attempted
- I followed everything stated in the installation.md found in the docs folder.
- 
## What Needs to Happen

## What I Have Found
- In the docs folder, I have read through all of the Jupiter notebooks and there appears to be three different trainers offered. You have NGBoost Trainer, Rust SmartCore Random Forest Trainer, and scikit-learn Random Forest Trainer. I don't know if we need to build a script though or where the script should be to start training.
- All three of those notebooks talked about using FASTSim, so I'm assuming that we have to do the same.
    - After further looking, it looks like we have to use FASTSim as a "physics" calculator that produces an energy consumption table. RouteE will then take that .csv and can quickly produce a new energy consumption table for any route that we want. Two things with this, RouteE requires the route to be a .csv as well. This means we need to be able to translate the route into a .csv file somehow. The second thing is after RouteE provides this energy consumption table, I think we will have to still implement the table into Matsim...