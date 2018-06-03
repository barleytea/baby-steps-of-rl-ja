import numpy as np


class Planner():

    def __init__(self, env):
        self.env = env

    @property
    def actions(self):
        return list(range(self.env.action_space.n))

    @property
    def states(self):
        return list(range(self.env.observation_space.n))

    def initialize(self):
        self.env.reset()

    def transitions_at(self, state, action):
        reward, done = self.env.reward_func(state)
        if not done:
            transition_probs = self.env.transit_func(state, action)
            for next_state in transition_probs:
                prob = transition_probs[next_state]
                reward, done = self.env.reward_func(next_state)
                yield prob, next_state, reward, done
        else:
            yield 1.0, None, reward, done

    def plan(self, gamma=0.9, threshold=0.0001):
        raise Exception("Planner have to implements plan method.")


class ValuteIterationPlanner(Planner):

    def __init__(self, env):
        super().__init__(env)

    def plan(self, gamma=0.9, threshold=0.0001):
        self.initialize()
        V = np.zeros(len(self.states))
        while True:
            delta = 0
            for s in self.states:
                expected_rewards = []
                for a in self.actions:
                    reward = 0
                    for p, n_s, r, done in self.transitions_at(s, a):
                        if n_s is None:
                            reward = r
                            continue
                        reward += p * (r + gamma * V[n_s] * (not done))
                    expected_rewards.append(reward)
                max_reward = max(expected_rewards)
                delta = max(delta, abs(max_reward - V[s]))
                V[s] = max_reward

            if delta < threshold:
                break

        return V


class PolicyIterationPlanner(Planner):

    def __init__(self, env):
        super().__init__(env)
        self.policy = None

    def initialize(self):
        super().initialize()
        self.policy = np.ones((self.env.observation_space.n,
                               self.env.action_space.n))
        # First, take each action uniformly.
        self.polidy = self.policy / self.env.action_space.n

    def estimate_by_policy(self, gamma, threshold):
        V = np.zeros(self.env.observation_space.n)

        while True:
            delta = 0
            for s in self.states:
                expected_rewards = []
                for a in self.actions:
                    action_prob = self.policy[s][a]
                    reward = 0
                    for p, n_s, r, done in self.transitions_at(s, a):
                        if n_s is None:
                            reward = r
                            continue
                        reward += action_prob * p * \
                                  (r + gamma * V[n_s] * (not done))
                    expected_rewards.append(reward)
                max_reward = max(expected_rewards)
                delta = max(delta, abs(max_reward - V[s]))
                V[s] = max_reward
            if delta < threshold:
                break
        return V

    def plan(self, gamma=0.9, threshold=0.0001):
        self.initialize()

        while True:
            update_stable = True
            # Estimate expected rewards under current policy
            V = self.estimate_by_policy(gamma, threshold)

            for s in self.states:
                # Get action following to the policy (choose max prob's action)
                policy_action = np.argmax(self.policy[s])

                # Compare with other actions
                action_rewards = np.zeros(len(self.actions))
                for a in self.actions:
                    reward = 0
                    for p, n_s, r, done in self.transitions_at(s, a):
                        if n_s is None:
                            reward = r
                            continue
                        reward += p * (r + gamma * V[n_s] * (not done))
                    action_rewards[a] = reward
                best_action = np.argmax(action_rewards)
                if policy_action != best_action:
                    update_stable = False

                # Update policy (set best_action prob=1, otherwise=0 (greedy))
                self.policy[s] = np.zeros(len(self.actions))
                self.policy[s][best_action] = 1.0

            if update_stable:
                # If policy isn't updated, stop iteration
                break

        return V


if __name__ == "__main__":
    def test_plan():
        from environment import GridWorldEnv
        env = GridWorldEnv(grid=[
            [0, 0, 0, 1],
            [0, 0, 0, 0],
            [0, -1, 0, 0],
            [0, 0, 0, 0],
        ])
        print("Value Iteration")
        vp = ValuteIterationPlanner(env)
        print(vp.plan().reshape(env.shape))

        print("Policy Iteration")
        pp = PolicyIterationPlanner(env)
        print(pp.plan().reshape(env.shape))

    test_plan()
