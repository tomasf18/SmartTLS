
from stable_baselines3.common.callbacks import BaseCallback

class AnalysisCallback(BaseCallback):
    """
    Custom callback for plotting additional values in tensorboard.
    """

    def __init__(self, env, verbose=0):
        super().__init__(verbose)
        self.env = env

    def _on_step(self) -> bool:
        
        accumulated_waiting_times = [info["total_accumulated_waiting"] for info in self.locals["infos"]]
        waiting_time = [sum(x) for x in zip(*accumulated_waiting_times)] # [private_wt, public_wt]

        rewards_sum = sum(self.locals["rewards"])
        
        self.logger.record("analysis/waiting_private_transport", waiting_time[0])
        self.logger.record("analysis/waiting_public_transport", waiting_time[1])
        self.logger.record("analysis/last_reward", rewards_sum)

        return True