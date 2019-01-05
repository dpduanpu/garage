import gym

from garage.contrib.exp import Agent
from garage.contrib.exp import Logger
from garage.contrib.exp import Checkpointer

class Experiment():
    def __init__(
            self,
            env: gym.Env,
            agent: Agent,
        checkpointer: Checkpointer,
            logger: Logger,
            sampler=None,
            # common experiment variant,
            n_itr=10,
            batch_size=1000,
            max_path_length=100,
            discount=0.99,
    ):
        if sampler is None:
            from garage.contrib.exp.samplers import BatchSampler
            sampler = BatchSampler(env=env, max_path_length=max_path_length)

        if checkpointer.resume:
            checkpoint = checkpointer.load(sampler=sampler, agent=agent)
            sampler = checkpoint['sampler']
            agent = checkpoint['agent']

        self.agent = agent
        self.checkpointer = checkpointer
        self.logger = logger
        self.sampler = sampler
        self.n_itr = n_itr
        self.batch_size = batch_size
        self.max_path_length = max_path_length
        self.discount = discount

        self.itr = 0

    def train_once(self):
        self.itr = self.itr + 1
        print('Itration', self.itr)

        obs = self.sampler.reset()
        while self.sampler.sample_count < self.batch_size:
            actions = self.agent.get_actions(obs)
            obs = self.sampler.step(actions)

        self.agent.train_once(self.sampler.get_samples())

    def train(self):
        while self.itr <= self.n_itr:
            self.train_once()

            print('Sampler Summary', self.sampler.get_summary())
            print('Agent Summary', self.agent.get_summary())

            self.checkpointer.next_epoch()
            self.checkpointer.save(sampler=self.sampler, agent=self.agent)
