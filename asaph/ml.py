"""
Copyright 2015 Ronald J. Nowling

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import random

import numpy as np

from sklearn.tree import DecisionTreeClassifier

class ConstrainedBaggingRandomForest(object):
    """
    Implementation of a Random Forest using constrained
    bagging for generating the training sets for the
    underlying Decision Trees.
    """

    def __init__(self, n_trees, n_resamples):
        self.n_trees = n_trees
        self.n_resamples = n_resamples

    def _resample(self, X, y):
        n_samples = X.shape[0] + self.n_resamples
        n_features = X.shape[1]
        
        X_new = np.zeros((n_samples, n_features))
        y_new = np.zeros(n_samples)

        for i in xrange(X.shape[0]):
            X_new[i, :] = X[i, :]
            y_new[i] = y[i]

        for i in xrange(X.shape[0], n_samples):
            idx = random.randint(0, X.shape[0] - 1)
            X_new[i, :] = X[idx, :]
            y_new[i] = y[idx]

        return X_new, y_new

    def _bootstrap(self, X, y):
        X_new = np.zeros(X.shape)
        y_new = np.zeros(X.shape[0])

        for i in xrange(X.shape[0]):
            idx = random.randint(0, X.shape[0] - 1)
            X_new[i, :] = X[idx, :]
            y_new[i] = y[idx]

        return X_new, y_new

    def feature_importances(self, X, y):
        feature_importances = np.zeros(X.shape[1])
        for i in xrange(self.n_trees):
            dt = DecisionTreeClassifier(max_features="sqrt")
            if self.n_resamples == -1:
                X_new, y_new = self._bootstrap(X, y)
            else:
                X_new, y_new = self._resample(X, y)
            dt.fit(X_new, y_new)
            feature_importances += dt.feature_importances_

        feature_importances = feature_importances / self.n_trees

        return feature_importances
        
