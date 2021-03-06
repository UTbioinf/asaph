"""
Copyright 2017 Ronald J. Nowling

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

import argparse
from collections import defaultdict
import itertools
import random
import os
import sys

import numpy as np

from asaph.newioutils import read_features
from asaph.cramers_v import cramers_v

from asaph.newioutils import deserialize
from asaph.newioutils import PROJECT_SUMMARY_FLNAME
from asaph.newioutils import serialize

onehot_to_ints = np.array([1, 2, 3])

def pair_association(pair1, pair2, features):
    snp_label1, feature_idx1 = pair1
    snp_label2, feature_idx2 = pair2

    # convert one-hot encoding back into integer encoding
    snp_features1 = np.dot(features.feature_matrix[:, feature_idx1],
                           onehot_to_ints)
    snp_features2 = np.dot(features.feature_matrix[:, feature_idx2],
                           onehot_to_ints)

    v = cramers_v(snp_features1,
                  snp_features2)

    return snp_label1, snp_label2, v

def sample_pairs(n_samples, items_one, items_two):
    sampled = set()
    while len(sampled) < n_samples:
        key1, value1 = random.choice(items_one)
        key2, value2 = random.choice(items_two)

        if key1 == key2:
            continue
        
        pair = frozenset([key1, key2])
        if pair in sampled:
            continue

        sampled.add(pair)
        yield (key1, value1), (key2, value2)

def pairwise_associations(features, flname, n_samples, set_one=None, set_two=None):
    next_output = 1

    snps_set_one = features.snp_feature_map
    if set_one:
        snps_set_one = dict()
        for key in set_one:
            if key in features.snp_feature_map:
                snps_set_one[key] = features.snp_feature_map[key]

    snps_set_one = snps_set_one.items()

    snps_set_two = features.snp_feature_map
    if set_two:
        snps_set_two = dict()
        for key in set_two:
            if key in features.snp_feature_map:
                snps_set_two[key] = features.snp_feature_map[key]

    snps_set_two = snps_set_two.items()

    if n_samples is not None:
        pairs = sample_pairs(n_samples, snps_set_one, snps_set_two)
    else:
        pairs = itertools.product(snps_set_one, snps_set_two)

    print "Found %s SNPs in set one" % len(snps_set_one)
    print "Found %s SNPs in set two" % len(snps_set_two)
    print "Evaluating", (len(snps_set_one) * len(snps_set_two)), "pairs"

    with open(flname, "w") as fl:
        for i, (pair1, pair2) in enumerate(pairs):
            snp_label1, snp_label2, v = pair_association(pair1,
                                                         pair2,
                                                         features)
            
            if i == next_output:
                print "Pair", i, "has an association of", v
                next_output *= 2

            chrom1, pos1 = snp_label1
            chrom2, pos2 = snp_label2
            fl.write("\t".join([chrom1, pos1, chrom2, pos2, str(v)]))
            fl.write("\n")

def pairwise_single_associations(features, stats_dir, chrom, pos):
    query_snp = (chrom, str(pos))
    if query_snp not in features.snp_feature_map:
        print "Unknown SNP:", str(query_snp)

    query_pair = (query_snp, features.snp_feature_map[query_snp])
    flname = "snp_associations_snp_%s_%s.txt" % (chrom, pos)

    with open(os.path.join(stats_dir, flname), "w") as fl:
        next_output = 1
        for i, pair in enumerate(features.snp_feature_map.iteritems()):
            if pair[0] == query_snp:
                continue
            
            snp_label1, snp_label2, v = pair_association(query_pair,
                                                         pair,
                                                         features)
            
            if i == next_output:
                print i, "SNP", pair[0], "has an association of", v
                next_output *= 2

            chrom, pos = snp_label2
            fl.write("\t".join([chrom, pos, str(v)]))
            fl.write("\n")

def pop_association_counts(pair, features, labels):
    snp_label, feature_idx = pair

    matrix = features.feature_matrix[:, feature_idx].astype(np.int32)
    n_samples, n_alleles = matrix.shape
    pop_labels = []
    allele_labels = []
    for i in xrange(n_samples):
        for j in xrange(n_alleles):
            for c in xrange(matrix[i, j]):
                pop_labels.append(labels[i])
                allele_labels.append(j)

    v = cramers_v(pop_labels,
                  allele_labels)

    return snp_label, v

def population_associations_counts(features, stats_dir):
    flname = "snp_population_associations.txt"
    with open(os.path.join(stats_dir, flname), "w") as fl:
        next_output = 1
        for i, pair in enumerate(features.snp_feature_map.iteritems()):
            snp_label, v = pop_association_counts(pair,
                                                  features,
                                                  features.class_labels)
            
            if i == next_output:
                print i, "SNP", pair[0], "has an association of", v
                next_output *= 2

            chrom, pos = snp_label
            fl.write("\t".join([chrom, pos, str(v)]))
            fl.write("\n")
        
def pop_association_categories(pair, features):
    snp_label, feature_idx = pair

    # convert one-hot encoding back into integer encoding
    snp_features = np.dot(features.feature_matrix[:, feature_idx],
                          onehot_to_ints)

    v = cramers_v(features.class_labels,
                  snp_features)

    return snp_label, v
            
def population_associations_categories(features, stats_dir):
    flname = "snp_population_associations.txt"
    with open(os.path.join(stats_dir, flname), "w") as fl:
        next_output = 1
        for i, pair in enumerate(features.snp_feature_map.iteritems()):
            snp_label, v = pop_association_categories(pair,
                                                      features)
            
            if i == next_output:
                print i, "SNP", pair[0], "has an association of", v
                next_output *= 2

            chrom, pos = snp_label
            fl.write("\t".join([chrom, pos, str(v)]))
            fl.write("\n")
            
def parseargs():
    parser = argparse.ArgumentParser(description="Asaph - Cramer's V")

    parser.add_argument("--workdir", type=str, help="Work directory", required=True)

    subparsers = parser.add_subparsers(dest="mode")

    pairwise_parser = subparsers.add_parser("pairwise",
                                            help="Compute pairwise association of SNPs")

    pairwise_parser.add_argument("--n-samples",
                                 type=int,
                                 help="Calculate on sampled pairs")

    pairwise_parser.add_argument("--subset-1",
                                 type=str,
                                 help="List of scaffolds and positions")

    pairwise_parser.add_argument("--subset-2",
                                 type=str,
                                 help="List of scaffolds and positions")

    pairwise_parser.add_argument("--output-fl",
                                 type=str,
                                 help="List of scaffolds and positions")

    single_parser = subparsers.add_parser("pairwise-single",
                                         help="Compute pairwise association versus a single SNP")

    single_parser.add_argument("--chrom",
                               type=str,
                               required=True)

    single_parser.add_argument("--pos",
                               type=int,
                               required=True)

    pop_parser = subparsers.add_parser("populations",
                                       help="Calculate association vs population structure")

    
    return parser.parse_args()

if __name__ == "__main__":
    args = parseargs()

    if not os.path.exists(args.workdir):
        print "Work directory '%s' does not exist." % args.workdir
        sys.exit(1)

    stats_dir = os.path.join(args.workdir, "statistics")
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)

    project_summary = deserialize(os.path.join(args.workdir, PROJECT_SUMMARY_FLNAME))
    
    features = read_features(args.workdir)

    if args.mode == "pairwise":
        if project_summary.feature_encoding != "categories":
            print "Pairwise Cramer's V only works with the 'categories' feature encoding."
            sys.exit(1)

        set_one = None
        if args.subset_1:
            with open(args.subset_1) as fl:
                set_one = set()
                for ln in fl:
                    cols = ln.strip().split()
                    set_one.add((cols[0], cols[1]))

        set_two = None
        if args.subset_2:
            with open(args.subset_2) as fl:
                set_two = set()
                for ln in fl:
                    cols = ln.strip().split()
                    set_two.add((cols[0], cols[1]))

        outfl = os.path.join(stats_dir, "snp_pairwise_associations.txt")
        if args.output_fl:
            outfl = os.path.join(stats_dir, args.output_fl)

        pairwise_associations(features,
                              outfl,
                              args.n_samples,
                              set_one=set_one,
                              set_two=set_two)
        
    if args.mode == "populations":
        if project_summary.feature_encoding == "categories":
            population_associations_categories(features,
                                               stats_dir)
        elif project_summary.feature_encoding == "counts":
            population_associations_counts(features,
                                           stats_dir)
        else:
            print "Unsupported feature encoding '%s'" % project_summary.feature_encoding
            sys.exit(1)
            
    elif args.mode == "pairwise-single":
        if project_summary.feature_encoding != "categories":
            print "Pairwise Cramer's V only works with the 'categories' feature encoding."
            sys.exit(1)

        pairwise_single_associations(features,
                                     stats_dir,
                                     args.chrom,
                                     args.pos)

