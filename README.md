# README

## Our Team 

| <div align="center"><a href="https://github.com/tomasf18"><img src="https://avatars.githubusercontent.com/u/122024767?v=4" width="150px;" alt="Tomás Santos"/></a><br/><strong>Tomás Santos</strong> | <div align="center"><a href="https://github.com/pedropintoo"><img src="https://avatars.githubusercontent.com/u/120741472?v=4" width="150px;" alt="Pedro Pinto"/></a><br/><strong>Pedro Pinto</strong> | <div align="center"><a href="https://github.com/DaniloMicael"><img src="https://avatars.githubusercontent.com/u/115811245?v=4" width="150px;" alt="Danilo Silva"/></a><br/><strong>Danilo Silva</strong> | <div align="center"><a href="https://github.com/jpapinto"><img src="https://avatars.githubusercontent.com/u/81636006?v=4" width="150px;" alt="João Pinto"/></a><br/><strong>João Pinto</strong> | <div align="center"><a href="https://github.com/Gui113893"><img src="https://avatars.githubusercontent.com/u/119808297?v=4" width="150px;" alt="Guilherme Santos"/></a><br/><strong>Guilherme Santos</strong> |
| --- | --- | --- | --- |


## 1. Setup

### 1.1 Create a Python Virtual Environment
```bash
python3 -m venv env
```

### 1.2 Activate the Virtual Environment
```bash
source env/bin/activate
```

### 1.3 Install Required Packages
```bash
pip install -r requirements.txt
```

## 2. Model Training and Testing

### 2.1 Train the Model
```bash
python3 train.py --save_model="data/<trained_model>" --simulation="cross/cross" --num_timesteps=100000
```

### 2.2 Test the Model
```bash
python3 test.py --load_model="data/<trained_model>" --simulation="cross/cross" --traffic_scale=1
```

### 2.3 Example Commands
```bash
python3 train.py --save_model="data/trained_model_ppo_aveiro_traffic" --simulation="aveiro_traffic/osm" --timesteps=200000
```
```bash
python3 test.py --load_model="data/trained_model_ppo_aveiro_traffic" --simulation="aveiro_traffic/osm" --traffic_scale=1
```

## 3. Visualization

### 3.1 Show TensorBoard
```bash
python3 -m tensorboard.main --logdir="./data/logs/"
```

### 3.2 Statistics Visualization
```bash
python3 $SUMO_HOME/tools/visualization/plotXMLAttributes.py teste.xml teste2.xml -x maxJamLengthInMeters -y @COUNT -i @NONE --legend --barplot --xbin 1 --xclamp :3000
```

## 4. Data Download

### 4.1 Download from osmWebWizard
Select the area in the opened website page and download the files:
```bash
python3 $SUMO_HOME/tools/osmWebWizard.py
```

## 5. Simulation Setup

### 5.1 Create a Simulation
1. Copy files to `sumo_config/<simulation_name>`.
2. Add `osm.det.xml` in the created folder:
   - In this file, you can add the detectors with the corresponding lanes (see in `netedit`).
3. Change the traffic light id in `netedit` in the file `osm.net.xml.gz` to **TLS**.
4. Start a test with the corresponding simulation parameters.

### 5.2 Run the Simulation (When No Simulation is Running)
Arguments:
- `data/trained_model_ppo_aveiro_traffic_1M_new` - The trained model.
- `2.75` - The traffic scale.
```bash
./stats.sh data/trained_model_ppo_aveiro_traffic_1M_new 2.75 
```

## 6. Simulation Data Generation (Without Shell)

### 6.1 Smart Traffic Light Model (Our Model)
Change `data/emissions.xml` to `data/emissions-smart.xml` and `data/waitingTime.xml` to `data/waitingTime-smart.xml`.
```bash
python3 test.py --load_model="data/trained_model_ppo_aveiro_traffic_1M_new" --simulation="aveiro_traffic/osm" --traffic_scale=2.75
```

### 6.2 Normal Traffic Light Model (No Model Used In Aveiro Yet)
Change `data/emissions.xml` to `data/emissions-normal.xml` and `data/waitingTime.xml` to `data/waitingTime-normal.xml`.
```bash
sumo -c sumo_config/aveiro_traffic/osm.sumocfg --tripinfo-output.write-unfinished="true" --duration-log.statistics="true" --device.emissions.probability="0.10" --no-step-log="true" --no-warnings="true" --end="2250" --scale="2.75" --start="true"
```

### 6.3 Actuated Traffic Light Model (Model Implemtented In Germany, "Gap-Based")
Change `data/emissions.xml` to `data/emissions-actuated.xml` and `data/waitingTime.xml` to `data/waitingTime-actuated.xml`.
```bash
sumo -c sumo_config/aveiro_traffic/osm.actuated.sumocfg --tripinfo-output.write-unfinished="true" --duration-log.statistics="true" --device.emissions.probability="0.10" --no-step-log="true" --no-warnings="true" --end="2250" --scale="2.75" --start="true"
```

### 6.4 Generate Graphs
```bash
python3 $SUMO_HOME/tools/visualization/plotXMLAttributes.py -x begin -y CO2_abs -i @NONE data/emissions-smart.xml data/emissions-normal.xml data/emissions-actuated.xml --ylabel="CO2 mg/m" --title="CO2 Emission in Traffic Lights" --legend --barplot --xbin=60
```
```bash
python3 $SUMO_HOME/tools/visualization/plotXMLAttributes.py -x begin -y waitingTime -i @NONE data/waitingTime-smart.xml data/waitingTime-normal.xml data/waitingTime-actuated.xml --ylabel="Time s/m" --title="Waiting Time in Traffic Lights" --legend --barplot --xbin=60
```

---

## Add a Simulation

### 1. Create the Simulation
Use the following command to create a simulation using the **osmWebWizard**:
```bash
python3 $SUMO_HOME/tools/osmWebWizard.py
```

### 2. Select the Desired City
- In the web interface, choose the region of interest by selecting the desired city or area for the simulation.

### 3. Modify Traffic Lights

1. Open the file `osm.net.xml.gz` in **NetEdit**.
2. Change the traffic light ID for each intersection to a sequential naming format:
    - **TLS1**, **TLS2**, ..., **TLSn**.

### 4. Add Detectors to the Simulation

1. Add detectors to the simulation by creating an `osm.det.xml` file in the same folder where the simulation files are located.
    - This file should define detectors and associate them with the corresponding lanes. You can look on `/sumo_config/aveiro_traffic/osm.det.xml`
    
2. Connect the detectors to the simulation configuration file `osm.sumocfg`.
    - This ensures the detectors are recognized and functional within the simulation.

### 5. Test the Simulation
Once the setup is complete, run the simulation using **sumo-gui** to visually verify the traffic flow and detector operations:
```bash
sumo-gui -c sumo_config/<simulation_name>/osm.sumocfg 
```

---
 
