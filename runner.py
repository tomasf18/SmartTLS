import os
import sys
import optparse
import random
from collections import defaultdict

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa

def _get_acumulated_waiting_time():
    """ Get the acumulated waiting time of the vehicles """
    waiting_time = 0
    for lane_id in traci.lanearea.getIDList():
        vehicles = traci.lanearea.getLastStepVehicleIDs(lane_id)
        
        for veh in vehicles:
            waiting_time += traci.vehicle.getAccumulatedWaitingTime(veh)
            
    return waiting_time

def run():
    """execute the TraCI control loop"""
    
    ## Tests
    
    print(traci)
    print(traci.trafficlight.getIDList())
    list_tls = traci.trafficlight.getIDList()
    filtered_tls = [tls for tls in list_tls if tls.startswith("TLS")]
    print("FILTERED TLS", filtered_tls)
    # Compacted version of the previous line
    filtered_tls = [tls for tls in traci.trafficlight.getIDList() if tls.startswith("TLS")]
    print("FILTERED TLS", filtered_tls)
    filtered_detectors = defaultdict(list)
    all_detectors = traci.lanearea.getIDList()
    for detector in all_detectors:
        tls = detector.split("_")[0]
        filtered_detectors[tls].append(detector)
    print("FILTERED DETECTORS", filtered_detectors)
    # Compacted version of the previous line
    filtered_detectors = defaultdict(list)
    for detector in traci.lanearea.getIDList():
        tls = detector.split("_")[0]
        filtered_detectors[tls].append(detector)
    
    print("Number of phases: ", len(traci.trafficlight.getAllProgramLogics("TLS1")[0].getPhases()))
    
    ## RUN
    step = 0
    
    # we start with phase 0 where NS has green
    traci.trafficlight.setPhase("TLS1", 0)
    accumulated_waiting_times = dict()
    currently_waiting = dict()
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        if step % 4 == 0:
            if traci.trafficlight.getPhase("TLS1") == 0:
                traci.trafficlight.setPhase("TLS1", 2) # set phase to 2
            else:
                traci.trafficlight.setPhase("TLS1", 0) # set phase to 0
        
        step += 1
        
        
        queue_length = traci.lanearea.getJamLengthVehicle("TLS1_Det1") / 100
        space_occupied = traci.lanearea.getLastStepOccupancy("TLS1_Det1") / 100
        mean_speed = traci.lanearea.getIntervalMeanSpeed("TLS1_Det1")

        observation = [queue_length, mean_speed, space_occupied]
        
        total_accumulated_waiting = 0
        for lane_id in traci.lanearea.getIDList():
            for vehicle in traci.lanearea.getLastStepVehicleIDs(lane_id):
                wt = traci.vehicle.getWaitingTime(vehicle)
                
                if wt == 0: # vehicle is not waiting
                    # Safely delete from currently_waiting
                    if lane_id in currently_waiting and vehicle in currently_waiting[lane_id]:
                        del currently_waiting[lane_id][vehicle]
                    # Add the accumulated waiting time if exists
                    if vehicle in accumulated_waiting_times and lane_id in accumulated_waiting_times[vehicle]:
                        total_accumulated_waiting += accumulated_waiting_times[vehicle][lane_id]
                    continue

                # Initialize or update the accumulated waiting time
                if vehicle not in accumulated_waiting_times: # never seen before
                    accumulated_waiting_times[vehicle] = {lane_id: wt}
                else:
                    if lane_id not in accumulated_waiting_times[vehicle]: # never seen before in this lane
                        accumulated_waiting_times[vehicle][lane_id] = wt
                    else:
                        accumulated_waiting_times[vehicle][lane_id] += wt - currently_waiting[lane_id].get(vehicle, 0)
                
                # Update currently waiting dictionary
                if lane_id not in currently_waiting:
                    currently_waiting[lane_id] = {}
                    
                currently_waiting[lane_id][vehicle] = wt
                total_accumulated_waiting += accumulated_waiting_times[vehicle][lane_id]
        
        
        
        print(total_accumulated_waiting)
                    
        # print(observation)
        # print(_get_acumulated_waiting_time())
        # print(traci.trafficlight.getDetectorVariable("TLS", "0", "vehicleCount"))
    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start([sumoBinary, "-c", "sumo_config/cross/cross.sumocfg"])
    run()