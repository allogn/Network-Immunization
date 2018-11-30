import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import helpers
import time
import logging
from collections import defaultdict, Counter

class SetSelector():

    def __init__(self, ranking, is_weighted=True):
        self.ranking = ranking
        self.is_weighted = is_weighted
        self.log = {}

    @staticmethod
    def get_best_score_mincut(scores, selected_nodes):
        best_key = None
        best_score = -1
        for s in scores:
            score = s[1]/SetSelector.get_cut_length_cost(s[0], selected_nodes) # score per node
            if score > best_score:
                best_score = score
                best_key = s[0]
        return best_key

    @staticmethod
    def get_updated_ranking(k, ranking, selected_nodes):
        vacant_node_set_size = k - len(selected_nodes)
        updated_ranking = defaultdict(lambda: [])
        sample_is_already_blocked = defaultdict(lambda: False)
        for key in ranking:
            if SetSelector.get_cut_length_cost(key, selected_nodes) > vacant_node_set_size:
                continue
            if helpers.set_in_set(key, selected_nodes):
                for sample_id in ranking[key]:
                    sample_is_already_blocked[sample_id] = True
            else:
                for sample_id in ranking[key]:
                    if not sample_is_already_blocked[sample_id]:
                        updated_ranking[key].append(sample_id)
        return updated_ranking

    @staticmethod
    def get_cut_length_cost(cut, selected_nodes):
        return len([1 for n in cut if n not in selected_nodes])

    @staticmethod
    def build_scores(ranking, selected_nodes):
        return SetSelector.build_weighted_scores(ranking, selected_nodes, defaultdict(lambda: 1))

    @staticmethod
    def build_weighted_scores(ranking, selected_nodes, weights_per_sample):
        scores = []
        for key in ranking:
            unique_sample_set = set()
            weight_of_sample_set = 0
            for key2 in ranking:
                if helpers.set_in_set(key2, key): # including itself
                    for n in ranking[key2]:
                        if n not in unique_sample_set:
                            weight_of_sample_set += weights_per_sample[n]
                            unique_sample_set.add(n)
            scores.append((key, weight_of_sample_set))
        return scores

    def get_best_nodes(self, k, strategy="basic"):
        selected_nodes = set()
        ranking = dict(self.ranking)
        it = 0
        while len(selected_nodes) < k:
            it += 1
            ranking = SetSelector.get_updated_ranking(k, ranking, selected_nodes)
            if self.is_weighted:
                sample_weights = self.get_sample_weights()
                scores = SetSelector.build_weighted_scores(ranking, selected_nodes, sample_weights)
            else:
                scores = SetSelector.build_scores(ranking, selected_nodes)
            new_nodes = SetSelector.get_best_score_mincut(scores, selected_nodes)
            if new_nodes == None:
                break
            for n in new_nodes:
                selected_nodes.add(n)
        self.log["Scores are weighted"] = self.is_weighted
        self.log["Blocking nodes selection iterations"] = it
        return selected_nodes

    def set_sampled_nodes_weights(self, p):
        # for exact estimator this is activation probabilities of sample nodes
        self.sampled_nodes_weights = p

    def set_sample_to_node_index(self, i):
        self.sample_to_node_index = i

    def get_positive_samples(self, blocked_set):
        return set(helpers.flatten([self.ranking[key] for key in self.ranking if helpers.set_in_set(key, blocked_set)]))

    def get_positive_node_counts(self, blocked_set):
        return Counter([self.sample_to_node_index[sample] for sample in self.get_positive_samples(blocked_set)])

    def get_predicted_normalized(self, iteration, blocked_set):
        return len(self.get_positive_samples(blocked_set))/(iteration+1)

    def get_predicted_normalized_per_node(self, blocked_set):
        all_samples_per_node = Counter(self.sample_to_node_index)
        positive_samples_per_node = self.get_positive_node_counts(blocked_set)
        result = 0
        for node in positive_samples_per_node:
            sampled_nodes_weights = self.get_sampled_nodes_weights()
            result += positive_samples_per_node[node]/all_samples_per_node[node]*sampled_nodes_weights[node]
        return result

    def get_sampled_nodes_weights(self):
        return self.sampled_nodes_weights

    def get_sample_weights(self):
        return [self.sampled_nodes_weights[n] for n in self.sample_to_node_index]
