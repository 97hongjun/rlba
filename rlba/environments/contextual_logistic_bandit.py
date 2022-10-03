# Copyright 2022 Morteza Ibrahimi. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A Contextual Logistic Bandit environment.
"""


import numpy as np
from rlba.types import (
    Array,
    ArraySpec,
    BoundedArraySpec,
    DiscreteArraySpec,
    NestedArraySpec,
    NestedDiscreteArraySpec,
)


class ContextualLogisticBandit:
    """This class creates a contextual logistic bandit environment."""

    def __init__(self, num_actions, num_contexts, dim, seed, sigma_p=1):
        self.num_actions = num_actions
        self.num_contexts = num_contexts
        self.dim = dim
        self.sigma_p = sigma_p
        self.sigma_p_squared = sigma_p**2
        self.theta = sigma_p * np.random.randn(dim)

        # Matrix of Phi_{S,A}
        feature = np.random.randn(num_contexts, num_actions, dim)
        self.feature = feature/np.linalg.norm(feature, axis=-1, keepdims=True)

        exp_logits = np.exp(np.tensordot(self.feature,
                                         self.theta, axes=([-1], [0])))

        # Reward Probabilities for each (S,A)
        self.rewards = exp_logits/(1 + exp_logits)
        # Maximum Reward for each context S
        self.values = np.max(self.rewards, axis=1, keepdims=True)
        # Matrix of Regrets
        self.regrets = self.values - self.rewards

        self._action_spec = DiscreteArraySpec(num_actions, name="action spec")
        self._observation_spec: ArraySpec = BoundedArraySpec(
            shape=(2,),
            dtype=int,
            minimum=0,
            maximum=num_contexts,
            name="observation spec",
        )
        self._reset_context()
        self._prev_context = None

    def _reset_context(self):
        """This function resets the context. For internal use only."""
        self.context = np.random.randint(low=0, high=self.num_contexts)
        self.context_features = self.feature[self.context, :, :]

    def expected_reward(self, action):
        return self.rewards[self._prev_context, action]

    def optimal_expected_reward(self):
        return np.max(self.rewards[self._prev_context])

    def _get_context(self):
        """ This function returns the current context and the associated feature. For internal use only.
            Use get_features() to obtain relevant information for your agent.
        """
        return self.context

    def output_means(self) -> Array:
        """ Returns a num_context x num_actions array of expected rewards  

           This method is for evaluation purposes only. It should not be used as part of
           agent/environment interaction.
        """
        return self.rewards

    def output_regrets(self) -> Array:
        """ Returns a num_context x num_actions array of expected regrets

            This method is for evaluation purposes only. It should not be used as part of
            agent/environment interaction.
        """
        return self.regrets

    def get_features(self, context_index) -> Array:
        """ Returns the features for each action associated with context context_index.
            Args:
                context_index: the integer index of the context for which you want features.
        """
        return self.feature[context_index, :, :]

    def step(self, action: int) -> Array:
        """ This function simulates for one step.
            Args:
                action: integer index of action to execute.

            TODO: make sure to update return description.
            Returns:
                An 'Observation' an Numpy Array of ints. Must conform to the
                specification returned by 'observation_spec()'
                Integer array [reward, context_index]
        """
        assert action >= 0 and action < self.num_actions

        mean_reward = self.rewards[self.context, action]
        reward = np.random.binomial(1, mean_reward)
        self._prev_context = self._get_context()
        self._reset_context()
        context_index = self._get_context()
        return np.array([reward, context_index]).astype(int)

    @property
    def observation_spec(self) -> NestedArraySpec:
        """Defines the observations provided by the environment.

        Returns:
          An `Array` spec, or a nested dict, list or tuple of `Array` specs.
        """
        return self._observation_spec

    @property
    def action_spec(self) -> NestedDiscreteArraySpec:
        """Defines the actions that should be provided to `step`.

        Returns:
          A `DiscereteArray` spec, or a nested dict, list or tuple of `DiscreteArray` specs.
        """
        return self._action_spec

    def close(self):
        """Frees any resources used by the environment.

        Implement this method for an environment backed by an external process.

        This method can be used directly

        ```python
        env = Env(...)
        # Use env.
        env.close()
        ```

        or via a context manager

        ```python
        with Env(...) as env:
          # Use env.
        ```
        """
        pass

    def __enter__(self):
        """Allows the environment to be used in a with-statement context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Allows the environment to be used in a with-statement context."""
        del exc_type, exc_value, traceback  # Unused.
        self.close()
