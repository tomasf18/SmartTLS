import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from marl_tls.env import TLSEnv
from marl_tls.analysis_callback import AnalysisCallback
import optparse

def get_options():
    optParser = optparse.OptionParser()
    
    optParser.add_option("--save_model", action="store", type="string", default="data/trained_model_ppo", help="file to load the model")
    optParser.add_option("--simulation", action="store", type="string", default="cross/cross", help="path to the simulation")
    optParser.add_option("--timesteps", action="store", type="int", default=100000, help="number of timesteps to train")
    optParser.add_option("--retrain_model", action="store", type="string", default=None, help="file to retrain the model")

    options, args = optParser.parse_args()
    return options

if __name__ == "__main__":
    options = get_options()
    
    save_model = options.save_model
    simulation_path = options.simulation
    timesteps = options.timesteps
    retrain_model = options.retrain_model

    end = 2250

    vec_env = TLSEnv.get_vec_env(
        TLSEnv,
        simulation_path=simulation_path,
        end=end
    ) 

    if retrain_model is None:
        # Train a new model
        model = PPO("MlpPolicy", vec_env, verbose=1, tensorboard_log="./data/logs")
        #model.learn(total_timesteps=timesteps, callback=AnalysisCallback(vec_env))
        model.learn(total_timesteps=timesteps, callback=AnalysisCallback(vec_env))
    else:
        # Retrain the model
        model = PPO.load(retrain_model, tensorboard_log="./data/logs")
        model.set_env(vec_env)
        model.learn(total_timesteps=timesteps, reset_num_timesteps=False, callback=AnalysisCallback(vec_env))

    model.save(save_model)
    vec_env.close()