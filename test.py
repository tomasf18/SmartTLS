import gymnasium as gym
import sys
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from marl_tls.env import TLSEnv
import optparse

def get_options():
    optParser = optparse.OptionParser()
    
    optParser.add_option("--load_model", action="store", type="string", default="data/trained_model_ppo", help="file to load the model")
    optParser.add_option("--simulation", action="store", type="string", default="cross/cross", help="path to the simulation")
    optParser.add_option("--traffic_scale", action="store", type="string", default="1", help="Scale Traffic")
    optParser.add_option("--render_mode", action="store", type="string", default="human", help="Render Mode")

    options, args = optParser.parse_args()
    return options

def run(vec_env, model, end):
    obs = vec_env.reset()
    step = 0
    while True:
        actions, _states = model.predict(obs)
        obs, rewards, dones, infos = vec_env.step(actions)
        step += 1
        if step >= end - 1: # end-1 because vec_env.reset() is called inside step() and starts a new simulation
            break

if __name__ == "__main__":
    options = get_options()

    load_model = options.load_model
    simulation_path = options.simulation
    traffic_scale = options.traffic_scale
    render_mode = options.render_mode

    model = PPO.load(load_model)
    
    end = 2250
    
    vec_env = TLSEnv.get_vec_env(
        TLSEnv,
        render_mode=render_mode if render_mode == "human" else None,
        simulation_path=simulation_path,
        traffic_scale=traffic_scale,
        end=end,
    ) # new environment with human visualization
    
    run(vec_env, model,end)
    vec_env.close()
    
    