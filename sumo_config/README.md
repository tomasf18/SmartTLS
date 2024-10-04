## Add a simulation

1. Create simulation with 
    ```bash
    python3 $SUMO_HOME/tools/osmWebWizard.py
    ```
2. Change the traffic light id in `netedit` in the file `osm.net.xml.gz` to **TLS1**, **TLS2**, etc.
3. Add detectors to the simulation
    - Add detectors (`osm.det.xml`) in the created folder
    - Connect the detectors in the simulation file `osm.sumocfg`.
4. Try to run the simulation with the following command
    ```bash
    sumo-gui -c sumo_config/<simulation_name>/osm.sumocfg 
    ```
