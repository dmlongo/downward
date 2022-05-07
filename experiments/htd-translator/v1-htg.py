#! /usr/bin/env python
# -*- coding: utf-8 -*-

import common_setup

from common_setup import IssueConfig, IssueExperiment

import os

from lab.reports import Attribute

from lab.environments import LocalEnvironment, BaselSlurmEnvironment

REVISIONS = [
    "release-21.12.0",
    "hypergrounding-v1",
]

CONFIGS = [
    IssueConfig(
        "translate-only",
        [],
        driver_options=["--translate"])
]

BENCHMARKS_DIR = os.environ["HTG_BENCHMARKS_FLATTENED"]
REPO = os.environ["DOWNWARD_REPO"]

if common_setup.is_running_on_cluster():
    SUITE = ['blocksworld-large-simple',
                 'childsnack-contents-parsize1-cham3',
                 'childsnack-contents-parsize1-cham5',
                 'childsnack-contents-parsize1-cham7',
                 'childsnack-contents-parsize2-cham3',
                 'childsnack-contents-parsize2-cham5',
                 'childsnack-contents-parsize2-cham7',
                 'childsnack-contents-parsize3-cham3',
                 'childsnack-contents-parsize3-cham5',
                 'childsnack-contents-parsize3-cham7',
                 'childsnack-contents-parsize4-cham3',
                 'childsnack-contents-parsize4-cham5',
                 'childsnack-contents-parsize4-cham7',
                 'genome-edit-distance',
                 'genome-edit-distance-split',
                 'logistics-large-simple',
                 'organic-synthesis-alkene',
                 'organic-synthesis-MIT',
                 'organic-synthesis-original',
                 'pipesworld-tankage-nosplit',
                 'rovers-large-simple',
                 'visitall-multidimensional-3-dim-visitall-CLOSE-g1',
                 'visitall-multidimensional-3-dim-visitall-CLOSE-g2',
                 'visitall-multidimensional-3-dim-visitall-CLOSE-g3',
                 'visitall-multidimensional-3-dim-visitall-FAR-g1',
                 'visitall-multidimensional-3-dim-visitall-FAR-g2',
                 'visitall-multidimensional-3-dim-visitall-FAR-g3',
                 'visitall-multidimensional-4-dim-visitall-CLOSE-g1',
                 'visitall-multidimensional-4-dim-visitall-CLOSE-g2',
                 'visitall-multidimensional-4-dim-visitall-CLOSE-g3',
                 'visitall-multidimensional-4-dim-visitall-FAR-g1',
                 'visitall-multidimensional-4-dim-visitall-FAR-g2',
                 'visitall-multidimensional-4-dim-visitall-FAR-g3',
                 'visitall-multidimensional-5-dim-visitall-CLOSE-g1',
                 'visitall-multidimensional-5-dim-visitall-CLOSE-g2',
                 'visitall-multidimensional-5-dim-visitall-CLOSE-g3',
                 'visitall-multidimensional-5-dim-visitall-FAR-g1',
                 'visitall-multidimensional-5-dim-visitall-FAR-g2',
                 'visitall-multidimensional-5-dim-visitall-FAR-g3']
    ENVIRONMENT = BaselSlurmEnvironment(
        partition="infai_2",
        export=["PATH", "HTG_BENCHMARKS_FLATTENED"],
    )
else:
    SUITE = ['genome-edit-distance:d-3-1.pddl']
    ENVIRONMENT = LocalEnvironment(processes=2)

exp = common_setup.IssueExperiment(
    revisions=REVISIONS,
    configs=CONFIGS,
    environment=ENVIRONMENT,
)

exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)

exp.add_step("build", exp.build)
exp.add_step("start", exp.start_runs)
exp.add_fetcher(name="fetch")

ATTRIBUTES = [
    'translator_time_done',
    'translator_mutex_groups',
    'translator_variables',
    'translator_time_computing_model',
    'translator_peak_memory',
    'translator_total_queue_pushes',
    'translator_final_queue_length',
    'translator_time_preparing_model'
]


exp.add_comparison_table_step(attributes=ATTRIBUTES)



exp.run_steps()
