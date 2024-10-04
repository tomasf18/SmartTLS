import os
import sys
import random
import functools
import gymnasium as gym
import numpy as np
from gymnasium import spaces
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
from sumolib import checkBinary
import traci

from collections import defaultdict

# Parallel Env
from pettingzoo import ParallelEnv
from pettingzoo.utils import agent_selector, wrappers
from stable_baselines3.common.vec_env import VecNormalize
import supersuit as ss

from typing import Union
from copy import copy
from sumo_config.sumo_utils import generate_route_file
from marl_tls.smart_tls import SmartTLS

PRIVATE_TRANSPORT_WEIGHT = 1
PUBLIC_TRANSPORT_WEIGHT = 5

from stable_baselines3.common.env_checker import check_env
from pettingzoo.test import parallel_api_test

class TLSEnv(ParallelEnv):
    metadata = {"render_modes": ["human"]}
    
    def __init__(
        self, 
        delta_time=5,               # Time steps to wait before changing the phase
        min_phase_time=5,           # Minimum time for a phase
        max_phase_time=120,         # Maximum time for a phase
        yellow_time=5,              # Yellow time
        traffic_scale=None,         # Scale traffic
        end=None,                   # Simulation end time
        render_mode=None,           # None or "human" for visualization
        simulation_path="cross/cross",  # Name of the simulation
        simulation_label="AveiroCity"   # Label for traci track communication
        ):
        """ Initialize the environment """
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        
        ## Start traffic simulation
        self.simulation_path = simulation_path
        self.simulation_label = simulation_label
        self.traffic_scale = traffic_scale
        self.episode_traffic_scale = 0
        
        self.sumo_start(hidden=True) # To get simulation data (e.g. detectors, tls, etc)
        self.end = end if end != None else traci.simulation.getEndTime()
        
        self.list_tls_id = [tls_id for tls_id in traci.trafficlight.getIDList() if tls_id.startswith("TLS")]
        
        self.list_tls = {
            tls_id: SmartTLS(
                tls_id=tls_id,
                delta_time=delta_time,
                min_phase_time=min_phase_time,
                max_phase_time=max_phase_time,
                yellow_time=yellow_time
            ) for tls_id in self.list_tls_id
        }
                
        ## Mandatory for ParallelEnv
        self.possible_agents = self.list_tls_id[:]
        self.agents = self.list_tls_id[:]  
        self.seed = None        

        self.observation_spaces = spaces.Dict(
            {tls_id: self.observation_space(tls_id) for tls_id in self.list_tls_id}
        )
        
        self.action_spaces = spaces.Dict(
            {tls_id: self.action_space(tls_id) for tls_id in self.list_tls_id}
        )
        
        ## Dicts for ParallelEnv
        self.rewards = {tls_id: 0 for tls_id in self.list_tls_id}
        self.terminations_false = {tls_id: False for tls_id in self.list_tls_id}
        self.terminations_true = {tls_id: True for tls_id in self.list_tls_id}
        self.truncations = {tls_id: False for tls_id in self.list_tls_id} # Not used
        self.infos = {tls_id: {} for tls_id in self.list_tls_id}
        
        ## Actions Time control
        self.current_step = 0
        self.delta_time = delta_time
        
        ## Cyclic stepping through the agents list
        self._agent_selector = agent_selector(self.list_tls_id) 
        self._agent_selection = self._agent_selector.next()
        
    
    @staticmethod
    def get_vec_env(cls, **kwargs):
        """ Return a vectorized version of the environment """
        env = cls(**kwargs)
        # parallel_api_test(env)
        
        ## Same observation and action spaces for all agents
        env = ss.pad_action_space_v0(env)
        env = ss.pad_observations_v0(env)
        
        vec_env = ss.pettingzoo_env_to_vec_env_v1(env)
        vec_env = ss.concat_vec_envs_v1(vec_env, 1, base_class="stable_baselines3")
        return vec_env
    
    def sumo_start(self, hidden=False):
        """ Start the sumo traci simulation """

        self.episode_traffic_scale = self.traffic_scale if self.traffic_scale != None else random.uniform(1,3.5)
        
        binary = checkBinary("sumo-gui") if self.render_mode == "human" and not hidden else checkBinary("sumo")
        
        start_input = [
            binary,
            "-c", "sumo_config/" + self.simulation_path + ".sumocfg",
            "--no-step-log", "true", 
            "--no-warnings", "true",
            "--scale", str(self.episode_traffic_scale),
        ]
        
        if self.render_mode == "human" and not hidden:
            start_input.extend([
                "--tripinfo-output.write-unfinished", "true",
                "--duration-log.statistics", "true",
                "--device.emissions.probability", "0.10"
            ])
        else:
            generate_route_file("sumo_config/" + self.simulation_path + ".rou.xml") # TODO: --random with seed!
            start_input.extend([
                "--quit-on-end", "true"
            ])
        
        traci.start(start_input, label=self.simulation_label)
    
    def _get_accumulated_waiting_time(self):
        """ Get the accumulated waiting time of the vehicles for all traffic lights """
        acumulated_waiting_times = [tls._get_accumulated_waiting_time() for tls in self.list_tls.values()]
        return [sum(x) for x in zip(*acumulated_waiting_times)] # [private_wt, public_wt]
    
    def _apply_actions(self, actions: Union[dict, int]):
        """ Apply the actions to the traffic lights """
        for tls_id, action in actions.items():
            tls = self.list_tls[tls_id]
            
            ## Update agent counters
            if not tls.action_available:
                tls.current_lock_time += 1
            else:
                tls.current_lock_time = 0
            
            ## Check if we need to change the phase to the aimed phase
            if tls.current_lock_time == tls.yellow_time:
                tls._set_phase(tls.aimed_phase)   # start the aimed phase
                tls.aimed_phase = None

            if tls.current_lock_time > tls.lock_time:
                tls.action_available = True

            if tls.action_available and self.current_step % self.delta_time == 0:
                tls._go_to_phase(action * 2)   # Mapping the action to the phase
    
    def _is_terminal(self):
        """ Check if the environment is in a terminal state """
        return self.current_step >= self.end # every tls has the same termination condition
    
    def reset(self, seed=None, options=None):

        self.agents = copy(self.possible_agents)
        traci.close()
        
        self.sumo_start()
        
        observations = {}
        infos = {}
        
        for tls in self.list_tls.values():
            observation, info = tls.agent_reset()
            observations[tls.tls_id] = observation
            infos[tls.tls_id] = info
        
        self.current_step = 0
        self._agent_selection = self._agent_selector.reset()
        
        return observations, infos

    def step(self, actions: Union[dict, int]):
        ## Apply actions
        self._apply_actions(actions)
        
        traci.simulationStep()
        self.current_step += 1
        
        ## Collect step information
        terminations = {tls.tls_id: self._is_terminal() for tls in self.list_tls.values()} 
        truncations = {tls.tls_id: False for tls in self.list_tls.values()} # Not used      
        rewards = {tls.tls_id: tls._get_reward() for tls in self.list_tls.values()}
        observations = {tls.tls_id: tls._get_observation() for tls in self.list_tls.values()}
        infos = {tls.tls_id: tls._get_info() for tls in self.list_tls.values()}

        return observations, rewards, terminations, truncations, infos
    
    
    def observe(self):
        """ Observe the environment """
        return {tls.tls_id: tls._get_observation() for tls in self.list_tls.values()}
    
    
    # lru_cache allows observation and action spaces to be memoized, reducing clock cycles required to get each agent's space.
    # IMPORTANT: If your spaces change over time, remove this lines (disable caching).
    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return self.list_tls[agent].observation_space

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return self.list_tls[agent].action_space

    def render(self):
        pass
    
    def close(self):
        traci.close()
    
    