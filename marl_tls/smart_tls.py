import os
import sys
import numpy as np
from gymnasium import spaces
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci
from collections import defaultdict
from operator import add;

PRIVATE_TRANSPORT_WEIGHT = 1
PUBLIC_TRANSPORT_WEIGHT = 5

class SmartTLS:
    
    def __init__(
        self,
        tls_id=None,                # Traffic Light id associated
        delta_time=5,               # Time steps to wait before changing the phase
        min_phase_time=5,           # Minimum time for a phase
        max_phase_time=120,         # Maximum time for a phase
        yellow_time=5               # Yellow time
        ):
        """ Initialize the agent """
        assert tls_id != None
        self.tls_id = tls_id
        
        self.delta_time = delta_time
        self.min_phase_time = min_phase_time
        self.max_phase_time = max_phase_time
        self.yellow_time = yellow_time

        ## Detector ID: TLS<tls_num>_Det<detector_num>
        self.lane_detectors = [detector_id for detector_id in traci.lanearea.getIDList() if detector_id.startswith(tls_id)]
        self.num_detectors = len(self.lane_detectors)

        ## Reward control
        self.last_reward = 0
        self.accumulated_waiting_times = defaultdict(lambda: defaultdict(int))
        self.currently_waiting = defaultdict(dict)
        
        ## Control parameters
        self.max_phase_time = max_phase_time    # TODO: not allow to exceed this value in a phase time
        self.num_phases = len(traci.trafficlight.getAllProgramLogics(tls_id)[0].getPhases())
        self.num_actions = int(self.num_phases / 2)
        
        ## Lock control
        self.yellow_time = yellow_time
        self.lock_time = yellow_time + min_phase_time
        self.current_lock_time = 0
        self.action_available = True
        
        ## Phase control
        # .current_phase  @property
        self.aimed_phase = None
        
        ## Observations
        self.observation_space = spaces.Box(
            low=np.array([0] * self.num_detectors + [0] + [0]),   # queue_weight (0 to 30), current_phase (0 to num_phases-1), action_available (0 or 1)
            high=np.array([30] * self.num_detectors + [self.num_phases - 1] + [1]),  # Upper bounds for each space
            dtype=np.int32
        )
        
        ## Actions
        self.action_space = spaces.Discrete(self.num_actions)    # {0, 1, ..., num_actions - 1}
     
    @property
    def current_phase(self):
        return traci.trafficlight.getPhase(self.tls_id)
     
    def agent_reset(self):
        """ Reset the agent """
        self.current_lock_time = 0
        self.action_available = True
        self.aimed_phase = None
        
        self.last_reward = 0
        self.accumulated_waiting_times = defaultdict(lambda: defaultdict(int))
        self.currently_waiting = defaultdict(dict)

        observation = self._get_observation()
        info = self._get_info()

        return observation, info
     
    def _get_queue_weight_obs(self):
        """ Queue weight of the vehicles in all detectors """
        weight_list = []
        
        for detector_id in self.lane_detectors:
            vehicles = traci.lanearea.getLastStepVehicleIDs(detector_id)
            weight = 0
            for veh in vehicles:
                veh_type = traci.vehicle.getTypeID(veh)
                
                if veh_type == "pt_bus":
                    weight += PUBLIC_TRANSPORT_WEIGHT
                else:
                    weight += PRIVATE_TRANSPORT_WEIGHT
            
            weight_list.append(weight)
            
        return weight_list
        
    def _get_observation(self):
        """ Observation of the environment """
        queue_weight = np.array(self._get_queue_weight_obs(), dtype=np.int32)
        
        return np.array(list(queue_weight) + [self.current_phase] + [int(self.action_available)], dtype=np.int32)
    
    def _get_info(self):
        """ Get the info of the environment """
        return {
            "total_accumulated_waiting": self._get_accumulated_waiting_time(),
            "current_phase": self.current_phase
        }
    
    def _set_phase(self, phase):
        """ Set the phase of the traffic light """
        traci.trafficlight.setPhase(self.tls_id, int(phase))    
    
    def _go_to_phase(self, phase): 
        """ **Asynchronously** go to the phase - the pending phase will be the aimed phase """  
        if self.current_phase == phase:
            return
        
        self.aimed_phase = phase
        self.action_available = False

        self._set_phase((self.current_phase + 1) % self.num_phases)   # start yellow phase (next phase)
        
    def _get_accumulated_waiting_time(self):
        """ Get the accumulated waiting time of the vehicles """
        total_accumulated_waiting = [0, 0] # [private_wt, public_wt]
        
        for detector_id in self.lane_detectors:
            for vehicle_id in traci.lanearea.getLastStepVehicleIDs(detector_id):
                waiting_time = traci.vehicle.getWaitingTime(vehicle_id)
                vehicleType = traci.vehicle.getTypeID(vehicle_id)
                
                if waiting_time == 0: # vehicle is not waiting
                    # Safely delete from currently_waiting
                    if detector_id in self.currently_waiting and vehicle_id in self.currently_waiting[detector_id]:
                        del self.currently_waiting[detector_id][vehicle_id]
                    # Add the accumulated waiting time if exists
                    if vehicle_id in self.accumulated_waiting_times and detector_id in self.accumulated_waiting_times[vehicle_id]:
                        total_accumulated_waiting[int(vehicleType == "pt_bus")] += self.accumulated_waiting_times[vehicle_id][detector_id]
                    continue
                
                # Update the accumulated waiting time
                if vehicle_id not in self.accumulated_waiting_times: # never seen before
                    self.accumulated_waiting_times[vehicle_id][detector_id] = waiting_time
                else: 
                    self.accumulated_waiting_times[vehicle_id][detector_id] += waiting_time - self.currently_waiting[detector_id].get(vehicle_id, 0)
    
                # Update currently waiting dictionary
                self.currently_waiting[detector_id][vehicle_id] = waiting_time
                total_accumulated_waiting[int(vehicleType == "pt_bus")] += self.accumulated_waiting_times[vehicle_id][detector_id]
                
        return total_accumulated_waiting

    def _get_reward(self):
        """ Get the reward of the environment """
        # Apply weights to prioritize public transport
        total_accumulated_waiting = np.array(self._get_accumulated_waiting_time()) * np.array([PRIVATE_TRANSPORT_WEIGHT, PUBLIC_TRANSPORT_WEIGHT])
        
        temp = np.sum(total_accumulated_waiting) / 100
        reward = self.last_reward - temp
        self.last_reward = temp
        return reward
    