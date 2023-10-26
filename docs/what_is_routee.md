# What is RouteE?

RouteE-Powertrain is a Python package that allows users to work with a set of pre-trained mesoscopic vehicle energy prediction models for a varity of vehicle types. Additionally, users can train their own models if "ground truth" energy consumption and driving data are available. RouteE-Powertrain models predict vehicle energy consumption over links in a road network, so the features considered for prediction often include traffic speeds, road grade, turns, etc. Common applications of RouteE-Powertrain are energy-aware ("eco") routing, energy accounting in mesoscopic simulations, and range estimation (especially for EVs). The diagrams below illustrate the logic and data flows for training custom RouteE-Powertrain models and performing prediction with previously trained models.

## Training
![image](https://github.com/NREL/routee-powertrain/assets/4818940/f5a89f64-241b-494b-9fe6-e13a34595da0)
Training new RouteE-Powertrain models requires a set of link aggregate driving data with energy consumption on each link in the road network. Often this data comes from high-frequency GPS or telematics data collected by dedicated loggers or from connected vehicles that are always streaming telematics data. The energy consumption can either be vehicle reported/measured or simulated using a powertrain simulation software like [NREL's FASTSim](https://github.com/NREL/fastsim).

## Prediction
![image](https://github.com/NREL/routee-powertrain/assets/4818940/b3a1d1af-5060-4bf4-a576-b0b11ffc9424)
In application, trained RouteE-Powertrain models expect link features as inputs and return predicted energy consumption for a particular vehicle over a link with the particular feature set. The RouteE developers maintain a separate repository for previously trained RouteE-Powertrain models, available for prediction "off the shelf".
