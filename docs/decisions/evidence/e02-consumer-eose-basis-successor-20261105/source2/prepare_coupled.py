"""Prepare an immutable coupled consumer SOURCE packet from genuine Root inputs.

This is a metadata/AST builder. It imports no project modules, executes no
models, and never follows operational helper descriptors. It grants nothing.
The only descriptor traversal is the finite typed selector program below.
"""
import argparse
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import tarfile

OWNED = Path(__file__).resolve().parent
PREDECESSOR = OWNED.parent / 'source1'
AUTHOR = '/root/consumer_coupled_source2'
SCOPE = OWNED.parent / 'coupled-source2-scope.json'
SCOPE_SHA = '0caa774f92853260ec787b1dd4180c81dc4aee6f8d1614f3ad117b9bc3b4b66f'
ENTRY_SHA = '82f905b4d20099f18c6b4218dfa5cfcbc134549e700e52f6cb62c2c9415d02d7'
SPEC_KEYS = ('schema actor rootScope predecessor captureSource captureSourceAcceptance '
             'admissionDataAcceptance producerControlData producerControlAcceptance '
             'helperComponentBasis actorAuthority basisVerificationEvidence controlClockSelection '
             'historicalNegativeInputAuthority callerClosure callerClosureEvidence preparationRecipe inputFiles').split()
FINAL = dict(CURRENT_CAPTURE_SOURCE='captureSource',
    CURRENT_CAPTURE_SOURCE_ACCEPTANCE='captureSourceAcceptance',
    CURRENT_ADMISSION_DATA_ACCEPTANCE='admissionDataAcceptance',
    CURRENT_PRODUCER_CONTROL_DATA='producerControlData',
    CURRENT_PRODUCER_CONTROL_ACCEPTANCE='producerControlAcceptance',
    CURRENT_HELPER_COMPONENT_BASIS='helperComponentBasis')
COUNTS = [129, 33, 29, 16, 20, 10, 11, 8, 7, 3, 20]
FORBIDDEN = ('/probe-root-custody-actual/', '/producer4-helper-probe-actual-',
             '65d8116b77bc0af1a108122ec28cfcea')
EXTRAS = ('model_stage.py', 'whole_window.py', 'prepare_consumer_edit.py',
          'prepare_observer_edit.py', 'strict_raw_method.txt',
          'whole_window_methods.txt', 'current_authority_methods.txt', 'README.md')
CLOCK_SHA = 'af211c44c3218c0cc71a882fbaddc78959571962e6198ef98546374417d89f16'
CLOCK_SCOPE = 'CURRENT_COUPLED_CONSUMER_PURE_CONTROL_REQUESTS_ONLY'
OPAQUE_SHA = 'a93e60d63670f07f4ddd543b6e68c2f3a4593c01eac531ee896c5ae0f7dcfa66'
FAILED_SHA = 'a24c34c90eb4480dcdc7f41d1ddde889a05d7c9e21a254c4131414cb80199926'
SPEC_KEYS.append('requiredFailedInventorySelection')


def validate_clock_selection(selection, control_names):
    closed(selection, ('schema actor scope predecessorControlPlan selection groups '
        'totalSerialOuterKillSeconds basis sourceRequirements helperAndControllerR10ClocksChanged '
        'ordinaryLeaseSeconds ordinaryClockChanged producer286ClockChanged '
        'modelExecutionAuthorized executionAuthorized').split(), 'CLOSED_ROOT_CONTROL_CLOCK_SELECTION')
    need(selection['schema'] == 'e02-root-consumer-pure-control-clock-source-selection-v1'
         and selection['actor'] == '/root' and selection['scope'] == CLOCK_SCOPE
         and selection['selection'] == 'FIXED_PER_GROUP_OUTER_KILL_BOUND_WITHOUT_RENEWAL',
         'EXACT_ROOT_CONTROL_CLOCK_SOURCE')
    need(selection['executionAuthorized'] is False and selection['modelExecutionAuthorized'] is False
         and selection['helperAndControllerR10ClocksChanged'] is False
         and selection['ordinaryClockChanged'] is False and selection['producer286ClockChanged'] is False
         and type(selection['ordinaryLeaseSeconds']) is int and selection['ordinaryLeaseSeconds'] == 1800,
         'SOURCE_CLOCK_SELECTION_ONLY_NO_OTHER_CLOCK_CHANGE')
    groups = selection['groups']
    need(type(groups) is list and [g['name'] for g in groups] == list(control_names)
         and len(groups) == 13 and len({g['name'] for g in groups}) == 13,
         'EXACT_THIRTEEN_CONTROL_CLOCK_NAMES')
    result = {}
    for group in groups:
        closed(group, ('name', 'definitions', 'outerKillSeconds'), 'EXACT_CONTROL_CLOCK_ROW')
        seconds = 120 if group['name'] == 'test_current_authority.py' else 63
        need(type(group['definitions']) is int and group['definitions'] > 0
             and type(group['outerKillSeconds']) is int and group['outerKillSeconds'] == seconds,
             'EXACT_NAME_SELECTED_FINITE_CONTROL_CLOCK')
        result[group['name']] = seconds
    need(type(selection['totalSerialOuterKillSeconds']) is int
         and selection['totalSerialOuterKillSeconds'] == sum(result.values()) == 876,
         'EXACT_SERIAL_CONTROL_CLOCK_LEDGER')
    return result


# Exact predecessor SOURCE and Root metadata seeds, never operational bodies.
# The immutable seven-hash denial is initialized before any seed is read.
DENIED_OPERATIONAL_HASHES = frozenset((
    '786ffa958ed73a04b36537969973522b15867aa5051cfa8127cf533d84deb84b',
    '3712e08db8d52c813a1e6ba6c7fe151e97fe3284fb36c00c8c1c0d79ef036a38',
    '938124c7f4d4da4f8a84a98e6f1eeb756024f720e2908bf9d37ea05a0263aa02',
    'ab29043bb9c535b5e1ccd95b8625834043a3064bb86b2a1c1fc0b3c8f20674b7',
    '6ef4c69d724875277e4b11127f923f327dcc3864a2beac434619cef656529efa',
    '26c46563fbbe53107a25ed7177862a07c4ff5f289476e146bcdba525a2d1ec2e',
    'ca1817971cd4188a6caacc700d54df3351056da7a09a8d56bea918912fc60de9'))
OPAQUE_EXPECTED_FROM_ROOT = {'/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-actual-r1/774675cbeebc22ae6a87b8b20795f539/output/cli-3-stdout.raw': {'path': '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-actual-r1/774675cbeebc22ae6a87b8b20795f539/output/cli-3-stdout.raw', 'bytes': 12633, 'sha256': 'a1dea229914c3b1baeac31a66d963958583c7d3780dfa6822553d355bc0d90f8'}, '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-actual-r1/774675cbeebc22ae6a87b8b20795f539/output/creation-intent.json': {'path': '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-actual-r1/774675cbeebc22ae6a87b8b20795f539/output/creation-intent.json', 'bytes': 1494, 'sha256': '255e940d083dfdaf013b30af3f4387adea611d84765c513b34492660bcd87218'}}
BOOTSTRAP_EXPECTED = {'/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/FINAL-FREEZE-INPUTS.UNISSUED.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/FINAL-FREEZE-INPUTS.UNISSUED.json', 'bytes': 2349, 'sha256': 'c4d5937dd5189650b9064219ffdc2a4284bbca9897ab8904f18c159a1eeee61f'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/HANDOFF.md': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/HANDOFF.md', 'bytes': 2934, 'sha256': '28e06268317d73d3a0172c72bd5363a45182844a96b5846c8efd06f9544d1102'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/authorized-ast-exceptions.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/authorized-ast-exceptions.json', 'bytes': 5086, 'sha256': 'a5efffb292b1b804b33c3eec0b0497c394bd3856ff59049056c09db0621cffe9'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/component-basis.UNISSUED.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/component-basis.UNISSUED.json', 'bytes': 20245, 'sha256': '5fe7d1aefddd2f793d17222d47de001ece72801baaece25d8824be71d49ab6b5'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/current-collector-prerequisite-contract.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/current-collector-prerequisite-contract.json', 'bytes': 8594, 'sha256': '19132d969f4f29aca3cc4919132b22c57221923001f6ecd84f350ff189f0539f'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/current-consumer-acceptance-contract.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/current-consumer-acceptance-contract.json', 'bytes': 5026, 'sha256': '03155edb0057833b2f5a2c815dd585f5f2286f1f40509742372ccbd966340f95'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/current-producer-data-acceptance-contract-286.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/current-producer-data-acceptance-contract-286.json', 'bytes': 2960, 'sha256': '51c0fe19a75680e9f665df6e4c71a3f71d05080adf36ce49f272715f8fe1469a'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/frozen-closed-contracts.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/contracts/frozen-closed-contracts.json', 'bytes': 44326, 'sha256': '4539cd1853b3dfd0b99cf730b5f01e6f3fb744716cb52fd3915cd6e047261787'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/development-checks.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/development-checks.json', 'bytes': 6464, 'sha256': 'd57a86aff5f1d7ccd812e424af9a21472783c687a1b1dd83b9624465bb68e8e6'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/fixture-authority.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/fixture-authority.json', 'bytes': 4136, 'sha256': '70e0bb133be1fa03f829d2b12ff5b744076f15725b507f52f678b957fbceeeb2'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/import-closure.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/import-closure.json', 'bytes': 49487, 'sha256': '71c299e2bf2fb1484e5cba09be291f692869336cf240ffaafdf0750f65ad1e04'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/input-read-map.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/input-read-map.json', 'bytes': 13919, 'sha256': '5ca50780fc9b8d36b97b796af96974dcb8ef741bd19af63bf3beae3f4a967fd3'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/negative-inputs.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/negative-inputs.json', 'bytes': 10405, 'sha256': '501305380d423b9cd282aa1e29edebd63b6052569e8999d7a1c473c3126e9803'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/ordinary-capture-projection.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/ordinary-capture-projection.json', 'bytes': 2032, 'sha256': 'faea09399ff7a8c273153ac4639f15e0937bf4c7936f1314216b70a6321ef71d'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/prepare_bundle.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/prepare_bundle.py', 'bytes': 17998, 'sha256': 'd725589929b5b668facb5d308a865545e63febdd8f76b75ba5df6d31c275d0eb'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/prepare_source.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/prepare_source.py', 'bytes': 3341, 'sha256': '9f90d0678355b8d954529ccfb5435391a44833e47b0f79acf5ce9911933b9cb9'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/preservation.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/preservation.json', 'bytes': 23900, 'sha256': '4e4689ca6189886d8629258f96d2346fd17589c8ffb91c7bf1b00aed0aec506d'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/requirements-and-coverage.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/requirements-and-coverage.json', 'bytes': 36507, 'sha256': '5b14086d255ed363d71cd74239d480453fbfc09b32326b59417ffdf9dafaea67'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/README.md': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/README.md', 'bytes': 2188, 'sha256': '96fc113da76a03c6c4ca2a2feecc1a7985fdb8d3fc4e1b439d213cdef91f1e5d'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/async_guard.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/async_guard.py', 'bytes': 11385, 'sha256': '1417fe474d8695196f5e9b441189993144313b4c5d2d2929e9d0a77c87dc7c68'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/capture_contracts.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/capture_contracts.py', 'bytes': 19017, 'sha256': 'cf491bf10d997bee6897aa42114c552e122f6f307db822851ece563999be204e'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/capture_outputs.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/capture_outputs.py', 'bytes': 3688, 'sha256': '32b1fcef306033557f736327916b9dfb532f5968bc457ccd85d1115a57f45621'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/collector_contracts.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/collector_contracts.py', 'bytes': 4201, 'sha256': '71027aeb69d409fbdcae19ff47be34c17b95106666e7f0e0459d1e87b6d48989'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/consumer.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/consumer.py', 'bytes': 86814, 'sha256': 'cd9e397607badcdb7946360b384009202162f463e6ee17212add80528a23763d'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/control-data-shape-contract.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/control-data-shape-contract.json', 'bytes': 1759, 'sha256': '07f5251a7b4ad1e6ec8ad5b5902dacccb927a574ea8c313284aef1f08d1f8082'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/control-plan.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/control-plan.json', 'bytes': 47015, 'sha256': 'a6eee6cb4116a8a8d6a4bed401e80a058bf00901528dfd9f9afea4d6dc047a0c'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/current_authority_methods.txt': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/current_authority_methods.txt', 'bytes': 12999, 'sha256': 'd10e266dc4cfdd22dcfcd7b4c738010ef84808348b19570dd988c8f47589a1b4'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/current_controls.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/current_controls.py', 'bytes': 10724, 'sha256': '6a06bd3fc6da9a7456b639529b186b87d6b17e2ab9be5201cc149478755b6b38'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/gui.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/gui.py', 'bytes': 14572, 'sha256': '1dc3dc2fffd258c9f9a638f7ccdd21c82becb4a3dab7261efb2459d572c2bad5'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/input-manifest.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/input-manifest.json', 'bytes': 3729, 'sha256': 'f9d4b2854a5fe0ef9424b47f152fb8b4c4bcce0d26ee84ebce47618e36bc3169'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/lineage.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/lineage.json', 'bytes': 1528, 'sha256': 'd121f9978ee4d4261398eba2453bd5bad20836127cd17b9f1b40361191a629ec'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/model_stage.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/model_stage.py', 'bytes': 8937, 'sha256': '0f947d6c9970027cdf82d7c4fe233684c1a64bac30582107d4e5f87acb5308a7'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/observer.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/observer.py', 'bytes': 23126, 'sha256': 'aca047cc7335c19cd620185ad21a0d8deb08d3c002cae15dd2cb2e5abc90d715'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/ordinary_capture_contracts.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/ordinary_capture_contracts.py', 'bytes': 31367, 'sha256': '4857cec19615dd81f7302a74a28b0cf7a0f8af832733a34b02c9bd075af83b88'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/ordinary_capture_outputs.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/ordinary_capture_outputs.py', 'bytes': 4917, 'sha256': 'eeaa2e5b2cdc7c3e5edec9232ae010507bfcfe723de7b58150653cda75f04a63'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/parent_allocation.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/parent_allocation.py', 'bytes': 6892, 'sha256': '0460f7b9077277ce3fb5164e3e50b45324742b86b6cd58b601667126c57554b6'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/prepare_consumer_edit.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/prepare_consumer_edit.py', 'bytes': 10232, 'sha256': '219c41b0049f41d4a16eb7b9898d3258bab808b959bbc33382760e304f6d51c5'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/prepare_observer_edit.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/prepare_observer_edit.py', 'bytes': 7536, 'sha256': 'b29a95ed2413363efcf19223e840a02bb826b050db7f1ccebe2c272b73be0f4e'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/probe_adapter.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/probe_adapter.py', 'bytes': 53667, 'sha256': '5a3a0859d29a758d6135ff983f9976aeb9a5ab9b8ec6641db576750ea98e4281'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/request_families.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/request_families.py', 'bytes': 11620, 'sha256': '29d98973b916060d94d98c954aa4a586586fe7f89e7dd557a49eee6a63519b68'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/runtime-gates.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/runtime-gates.json', 'bytes': 1134, 'sha256': '2bac588521941bfd582b021fd520f606791b1604fa1d5f211508ec571e0f47e2'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/static-preparation.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/static-preparation.json', 'bytes': 286, 'sha256': 'd685160495a9f28569b94669fb0d7cfc32b7e57d59e7e7443e3662225e3d331e'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/strict.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/strict.py', 'bytes': 12898, 'sha256': '1bb1acaa173d1383d0aaef60130c4379b97b5e1d8014a8e73998639ed18430a3'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/strict_raw_method.txt': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/strict_raw_method.txt', 'bytes': 2181, 'sha256': '7799d75a2f22c9c5643ad3cebe52a5384a069c097c6e9e9d1157accd77dea0e6'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/subject.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/subject.json', 'bytes': 20272, 'sha256': 'fbc839af74bdbb9886f52e4c29ebb594fcc54a36c83f4106bf22ced5aa2a2056'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_async_guard.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_async_guard.py', 'bytes': 10240, 'sha256': 'd29ef53d04f81e2e51f1b2c498c5b8d8fb51a11335e5c4b3b1e077f1c7b04b78'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_component_basis.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_component_basis.py', 'bytes': 29435, 'sha256': '034b49489fa226879ddcd64008892f8595d39ca74589e61bcef153c1223c5818'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_current_authority.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_current_authority.py', 'bytes': 52760, 'sha256': 'ab7f4005cdad2f5955c9ba10e2ab4b51a3fd7c5bfe8d2a77926240d0b053401f'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_current_controls.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_current_controls.py', 'bytes': 10395, 'sha256': 'eb741c777dd96ec367eda07937429b082b9c80f3d4b82cb9b000385018a4cc2e'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_data_controls.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_data_controls.py', 'bytes': 43425, 'sha256': '4cce7a04508ff87ca0546983f97897be2e5d95d3a7fc5bf5e0e568af45923365'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_import_closure.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_import_closure.py', 'bytes': 11765, 'sha256': '17016fc0873ce62c7267369f1f1910532170740ebba703be55848fc74bee049f'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_mode_reader.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_mode_reader.py', 'bytes': 9326, 'sha256': 'a4e497dc09a7c8eb61d816018a7b446d8e6a2cc5750058df040e6ae5cc7cd37a'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_observer_v3.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_observer_v3.py', 'bytes': 3521, 'sha256': 'b86e06ad8d86bd8d6d88018a91c46458e4606093feedea47477a9cc1ea1bf565'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_parent_allocation.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_parent_allocation.py', 'bytes': 7718, 'sha256': 'f7350352aa4e2659d953ed37c4a2af3762bfd0b6201456343868144274dc65ed'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_probe_adapter.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_probe_adapter.py', 'bytes': 9700, 'sha256': 'e9676d081b00ec85f9e365c06d22f4ba420be4719afed9799d8df9d242798533'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_request_families.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_request_families.py', 'bytes': 14614, 'sha256': '0a35acbd1670c8e0825ae96c0c54b3c1ac6e8a31c6b8c451d9a82169a3c8a43c'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_source_bindings.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_source_bindings.py', 'bytes': 5946, 'sha256': 'b158f594bc41fe48f9647350d401ae4d1c971dd19768cbbd9a09b5bbd766d2ed'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_whole_window.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/test_whole_window.py', 'bytes': 8221, 'sha256': 'e7e5a2dfa873e9e630ce309d63b4d8ee5401ceaacb9c8a04e62f48a504a81cc1'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/whole_window.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/whole_window.py', 'bytes': 57972, 'sha256': 'ca6c7939b291748b495c73de32a8b41912d1ed89871dd803b671df8479180ecc'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/whole_window_methods.txt': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/whole_window_methods.txt', 'bytes': 8132, 'sha256': 'f32efaeec213ed0444cc01a4fc673575b2b2028c5e37977d53ef358e1e34702c'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/wire.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/wire.py', 'bytes': 20120, 'sha256': 'aa06718b30992c565ca7fcec721a5e3badebc6ad06f76ac11ebde09870932596'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/witness.py': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source/witness.py', 'bytes': 19960, 'sha256': 'ce98436428fdcac553b6ef7e8452fedc9e0f5dfbc1d5f187c2a7ceb46014f377'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source-delta.patch': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source-delta.patch', 'bytes': 127881, 'sha256': '7070af9f01665df97f97fb29f785ea58e8002953a366b6290296e142ca096086'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/unbound-status.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/unbound-status.json', 'bytes': 1952, 'sha256': '4655e1deb304578d9fb27d97f8620a59ce7d7818e9857ef699b82d63444ce328'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/entrypoint.UNBOUND.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/entrypoint.UNBOUND.json', 'bytes': 2862, 'sha256': '82f905b4d20099f18c6b4218dfa5cfcbc134549e700e52f6cb62c2c9415d02d7'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source.UNBOUND.tar': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/source.UNBOUND.tar', 'bytes': 1177600, 'sha256': '0f8293cc238742118591abbd06113f7a0e558d26acfb3c7967fa5ce3ebf8b869'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/baseline-metadata/input-manifest.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source1/baseline-metadata/input-manifest.json', 'bytes': 234543, 'sha256': '7f5ff81d311e80484d5db718316fb9998d5869264ae1c7590bdc62fe5763a491'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/coupled-source2-scope.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/coupled-source2-scope.json', 'bytes': 3185, 'sha256': '0caa774f92853260ec787b1dd4180c81dc4aee6f8d1614f3ad117b9bc3b4b66f'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-coupled-actor-authority.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-coupled-actor-authority.json', 'bytes': 14019, 'sha256': 'f80baccad749289f022e45784c288548bece4ad72c527f86e9e1da2e4f54f16d'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-consumer-control-clock-selection.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-consumer-control-clock-selection.json', 'bytes': 3323, 'sha256': 'af211c44c3218c0cc71a882fbaddc78959571962e6198ef98546374417d89f16'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-historical-negative-opaque-source-decision.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-historical-negative-opaque-source-decision.json', 'bytes': 2134, 'sha256': 'a93e60d63670f07f4ddd543b6e68c2f3a4593c01eac531ee896c5ae0f7dcfa66'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-caller-closure-r2/caller-closure-input.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-caller-closure-r2/caller-closure-input.json', 'bytes': 31542, 'sha256': '2a3e5d5b2029918299f0797edd092a497fba72daf92b3f48c6d9ecc4d444dc64'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-caller-closure-r2/preparation-evidence.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-caller-closure-r2/preparation-evidence.json', 'bytes': 19243, 'sha256': '88f27bbdbab6c4b291bfa88c7be6d35ac1811ca094f9d25e9c6411fbe4563685'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-capture-20261105/source2/capture/code-subject.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-capture-20261105/source2/capture/code-subject.json', 'bytes': 10552, 'sha256': '4e678b19ebe954207011e98f97ed8acef81a00328c3ae014f6d433ef648c21b7'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-capture-review-20261105/source2/acceptance.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-capture-review-20261105/source2/acceptance.json', 'bytes': 1408, 'sha256': '900842f2d3e7e0e74de112316b79af1c606708456e280dab49d3ca14f6a497bc'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-capture-admission-eose-model-20261105/r1/acceptance.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-capture-admission-eose-model-20261105/r1/acceptance.json', 'bytes': 2015, 'sha256': '112b9ee6a7df3df274d58b8f325d3af71c2b00aa8692783a9cd12c4cddf068cb'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-current286-data-review-20261105/r1/acceptance.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-current286-data-review-20261105/r1/acceptance.json', 'bytes': 3845, 'sha256': 'a6d2f2830b9507df3b9ffb4ce64981dea60058034feaf13852b08661a92607f0'}, '/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-eose-6ea9fb8bcdd736d1d54000e4/assembled/subject.json': {'path': '/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-eose-6ea9fb8bcdd736d1d54000e4/assembled/subject.json', 'bytes': 4116, 'sha256': '9d64ecd4ae07efa474a842b7eb0a48ff97be901e64144e18e56dc2ca483df0f9'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-helper-component-basis-contract-20261105/source1/component-basis.UNISSUED.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-helper-component-basis-contract-20261105/source1/component-basis.UNISSUED.json', 'bytes': 20245, 'sha256': '5fe7d1aefddd2f793d17222d47de001ece72801baaece25d8824be71d49ab6b5'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-helper-current178-actual-review-20261105/r2/acceptance.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-helper-current178-actual-review-20261105/r2/acceptance.json', 'bytes': 3893, 'sha256': '85c6d73d8e20703fbfac671c5b5b3d1b0c215e9b2f5cee0043052e9f3d614238'}, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-helper-current178-actual-review-20261105/r2/final-closure-descriptor.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-helper-current178-actual-review-20261105/r2/final-closure-descriptor.json', 'bytes': 1084, 'sha256': 'c74428b7a2612ff4b1801b54b39a63088050e5c31db078e9e5d8ab78efc22e54'}}
BOOTSTRAP_EXPECTED['/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-required-failed-inventory-selection.json'] = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/root-required-failed-inventory-selection.json', 'bytes': 17236, 'sha256': 'a24c34c90eb4480dcdc7f41d1ddde889a05d7c9e21a254c4131414cb80199926'}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def closed(value, keys, reason):
    need(type(value) is dict and set(value) == set(keys), reason)


def pin_shape(value):
    closed(value, ('path', 'bytes', 'sha256'), 'EXACT_DESCRIPTOR_KEYS')
    need(type(value['path']) is str and Path(value['path']).is_absolute()
         and os.path.normpath(value['path']) == value['path'], 'CANONICAL_ABSOLUTE_PIN')
    need(type(value['bytes']) is int and 0 <= value['bytes'] <= 16777216,
         'BOUNDED_SOURCE_METADATA_PIN')
    need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']),
         'EXACT_SHA256')
    return value


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def descriptor(path, body):
    return dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


def identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


class Reader:
    """Bounded nofollow, identity-continuous SOURCE/pure-control reads only."""
    def __init__(self, require_pre_admission=False):
        self.denied_hashes = DENIED_OPERATIONAL_HASHES
        self.require_pre_admission = require_pre_admission
        self.capabilities = {}
        self.observed = {}

    def admit(self, pins):
        need(type(pins) is list and len(pins) <= 20000, 'FINITE_SOURCE_INPUT_CAPABILITIES')
        checked = {}
        for pin in pins:
            pin_shape(pin)
            need(pin['sha256'] not in self.denied_hashes, 'OPERATIONAL_HELPER_HASH_FORBIDDEN_BEFORE_READ')
            if any(part in pin['path'] for part in FORBIDDEN):
                need(OPAQUE_EXPECTED_FROM_ROOT.get(pin['path']) == pin,
                     'FORBIDDEN_OPERATIONAL_SOURCE_CAPABILITY')
                continue  # Retained expected-only operand; never a read capability.
            old = self.capabilities.get(pin['path'])
            need(old is None or old == pin, 'SOURCE_CAPABILITY_PIN_SUBSTITUTION')
            need(pin['path'] not in checked or checked[pin['path']] == pin, 'SOURCE_CAPABILITY_LIST_CONFLICT')
            checked[pin['path']] = pin
        # Commit only after every descriptor has passed; no source I/O occurs.
        self.capabilities.update(checked)

    def read(self, path, expected=None, mode=None):
        path = Path(path)
        text = str(path)
        need(path.is_absolute() and os.path.normpath(text) == text,
             'CANONICAL_READ_PATH')
        need(not any(part in text for part in FORBIDDEN),
             'OPERATIONAL_HELPER_BODY_FORBIDDEN_DURING_SOURCE_PREPARATION')
        if expected is None:
            expected = self.capabilities.get(text) or BOOTSTRAP_EXPECTED.get(text)
        need(expected is not None, 'UNKNOWN_SOURCE_READ_WITHOUT_EXPECTED_CAPABILITY')
        pin_shape(expected)
        need(expected['path'] == text, 'EXACT_CAPABILITY_PATH')
        need(expected['sha256'] not in self.denied_hashes,
             'OPERATIONAL_HELPER_HASH_FORBIDDEN_BEFORE_READ')
        if self.require_pre_admission:
            need(self.capabilities.get(text) == expected, 'SOURCE_INPUT_NOT_PREADMITTED')
        for parent in (path, *path.parents):
            need(not parent.is_symlink(), 'NO_SYMLINK_READ_ALIAS')
        first = path.lstat()
        need(stat.S_ISREG(first.st_mode) and first.st_size <= 16777216,
             'BOUNDED_REGULAR_SOURCE_OR_METADATA')
        if mode is not None:
            need(stat.S_IMODE(first.st_mode) == mode, 'EXACT_SOURCE_MODE')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            need(identity(os.fstat(fd)) == identity(first), 'OPEN_IDENTITY_CONTINUITY')
            chunks = []
            size = 0
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                need(size <= first.st_size, 'READ_BOUND_CONTINUITY')
            need(identity(os.fstat(fd)) == identity(first), 'HANDLE_IDENTITY_CONTINUITY')
        finally:
            os.close(fd)
        body = b''.join(chunks)
        need(len(body) == first.st_size and identity(path.lstat()) == identity(first),
             'PATH_IDENTITY_CONTINUITY')
        actual = descriptor(path, body)
        if expected is not None:
            pin_shape(expected)
            need(actual == expected, 'EXACT_EXPECTED_INPUT_PIN')
        if text in self.observed:
            need(self.observed[text] == (actual, identity(first)), 'REPEATED_INPUT_IDENTITY')
        self.observed[text] = (actual, identity(first))
        return actual, body

    def doc(self, pin):
        pin_shape(pin)
        _, body = self.read(pin['path'], pin)
        def pairs(items):
            result = {}
            for key, value in items:
                need(key not in result, 'DUPLICATE_METADATA_KEY')
                result[key] = value
            return result
        def no_float(value):
            raise ValueError('INTEGER_ONLY_SOURCE_METADATA')
        return json.loads(body.decode('utf8', 'strict'), object_pairs_hook=pairs,
                          parse_float=no_float, parse_constant=no_float)

    def recheck(self):
        for path, (pin, first) in list(self.observed.items()):
            need(identity(Path(path).lstat()) == first, 'FINAL_SOURCE_INPUT_IDENTITY')
            self.read(path, pin)


def assignments(body):
    values = {}
    for node in ast.parse(body).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return values


def methods(body):
    return {cls.name + '.' + method.name: ast.dump(method, include_attributes=False)
            for cls in ast.parse(body).body if isinstance(cls, ast.ClassDef)
            for method in cls.body if isinstance(method, ast.FunctionDef)
            and method.name.startswith('test_')}


def reviews(reader, pins, subject, decision, forbidden):
    need(type(pins) is list and len(pins) == 2, 'TWO_ORDERED_INDEPENDENT_REVIEWS')
    sessions = []
    for role, pin in zip(('qa', 'security'), pins):
        value = reader.doc(pin)
        closed(value, ('role', 'session', 'decision', 'subject'), 'CLOSED_REVIEW_ENVELOPE')
        need(value['role'] == role and value['decision'] == decision
             and value['subject'] == subject, 'EXACT_ACTUAL_REVIEW_JOIN')
        need(type(value['session']) is str and value['session'].startswith('/root/')
             and value['session'] not in forbidden, 'REVIEWER_OUTSIDE_FROZEN_ACTORS')
        sessions.append(value['session'])
    need(len(set(sessions)) == 2, 'DISTINCT_REVIEWERS')


def validate_caller_closure(reader, pin, evidence_pin, authority_pin, participants):
    """Strict v2 projection over real selected actor fields, never an eight-key fallback."""
    need(pin is not None and evidence_pin is not None, 'MANDATORY_ROOT_CALLER_CLOSURE_INPUT')
    need(pin['sha256'] == '2a3e5d5b2029918299f0797edd092a497fba72daf92b3f48c6d9ecc4d444dc64'
         and evidence_pin['sha256'] == '88f27bbdbab6c4b291bfa88c7be6d35ac1811ca094f9d25e9c6411fbe4563685',
         'EXACT_ROOT_SELECTED_CALLER_V2_AND_EVIDENCE_PINS')
    value = reader.doc(pin)
    closed(value, ('schema actor scope actorAuthority executionAuthorized declarations').split(),
           'CLOSED_SIX_KEY_ROOT_CALLER_V2')
    need(value['schema'] == 'e02-helper-component-basis-caller-closure-input-v2'
         and value['actor'] == '/root' and value['scope'] == 'SOURCE_MAPPING_CALLER_ACTOR_SUBSETS_ONLY'
         and value['actorAuthority'] == authority_pin and value['executionAuthorized'] is False,
         'EXACT_ROOT_CALLER_V2_AUTHORITY_NO_V1_FALLBACK')
    evidence = reader.doc(evidence_pin)
    need(evidence['schema'] == 'e02-root-caller-closure-v2-preparation-evidence-v1'
         and evidence['actor'] == '/root' and evidence['callerClosure'] == pin
         and evidence['failedAttempts'] == 15 and evidence['existingLegacyNodes'] == 63
         and evidence['declarationRows'] == 26 and evidence['fixedAllowedCallers'] == len(participants) == 75
         and evidence['helperBodyReads'] == 0 and evidence['actualFutureArtifactsIssued'] is False
         and evidence['newPhysicalInputRehashClaimed'] is False and evidence['executionAuthorized'] is False,
         'ROOT_CALLER_V2_SCOPE_AND_COMPLETENESS')
    need(evidence['transform'] == dict(changedKeys=['schema'],
        fromSchema='e02-helper-component-basis-caller-closure-input-v1',
        toSchema='e02-helper-component-basis-caller-closure-input-v2',
        declarationsUnchanged=True, authorOperatorSplitsInvented=False),
        'DISCLOSED_V1_TO_V2_SCHEMA_ONLY_TRANSFORM')
    prior = reader.doc(evidence['priorCallerClosure'])
    need(prior['schema'] == 'e02-helper-component-basis-caller-closure-input-v1'
         and prior['declarations'] == value['declarations'], 'PRESERVED_INITIAL_PROJECTION')
    for expected in evidence['inputs']:
        reader.read(expected['path'], expected)
    declarations = value['declarations']
    expected_fields = [('legacy', '/legacyActors')] + [('attempt', '/actors')] * 14 + [
        ('attempt', '/authors'), ('attempt', '/operators'),
        ('candidate', '/authors'), ('candidate', '/operators'),
        ('sourceControls', '/authors'), ('sourceControls', '/operators'),
        ('candidate', '/futureCandidate/allowedActors'), ('history', '/futureHistory/allowedActors'),
        ('sourceControls', '/futureSourceControls/allowedActors'),
        ('futureWindow', '/futureWindows/incoming/allowedActors'),
        ('futureWindow', '/futureWindows/archive/allowedActors')]
    need(type(declarations) is list and len(declarations) == len(expected_fields) == 26,
         'ALL_TWENTYSIX_FINITE_CALLER_V2_FIELDS')
    def pointer(document, selector):
        need(type(selector) is str and selector.startswith('/'), 'EXPLICIT_ACTOR_FIELD_POINTER')
        for token in selector[1:].split('/'):
            document = document[int(token)] if type(document) is list else document[token]
        return document
    def selected_actors(subject, selector):
        observed = pointer(reader.doc(subject), selector)
        if type(observed) is str:
            observed = [observed]
        need(type(observed) is list and observed and all(type(actor) is str
             and (actor == '/root' or actor.startswith('/root/')) for actor in observed),
             'EXACT_NONEMPTY_SELECTED_ACTOR_FIELD')
        # v2 is a caller-set projection. Original ordering remains protected by
        # the complete source descriptor; the projected field is canonical.
        return sorted(set(observed))
    for row, (role, selector) in zip(declarations, expected_fields):
        closed(row, ('role', 'subject', 'selector', 'actors'), 'CLOSED_CALLER_FIELD_DECLARATION')
        need(row['role'] == role and row['selector'] == selector,
             'EXACT_TYPED_CALLER_V2_ROLE_AND_SELECTOR_VECTOR')
        observed = selected_actors(row['subject'], selector)
        need(row['actors'] == observed and set(observed) <= participants,
             'ALL_CALLER_V2_ACTORS_WITHIN_FROZEN_AUTHORITY')
    legacy = reader.doc(declarations[0]['subject'])
    registry = reader.doc(evidence['historicalRegistry'])
    need(legacy['registry'] == evidence['historicalRegistry']
         and len(registry['legacyActorNodes']) == len(legacy['finiteNodes']) == 63,
         'EXACT_SIXTYTHREE_LEGACY_NODE_INVENTORY')
    registry_pins = {entry['pin']['path']: entry['pin'] for entry in registry['legacyActorNodes'].values()}
    need({item['path']: item for item in legacy['finiteNodes']} == registry_pins,
         'ALL_EXPLICIT_REGISTRY_NODES_PRESERVED')
    for item in legacy['finiteNodes']:
        reader.read(item['path'], item)
    union = set()
    for proof in legacy['selectedFieldProofs']:
        closed(proof, ('subject', 'selector', 'actors'), 'CLOSED_LEGACY_ACTOR_FIELD_PROOF')
        need(registry_pins.get(proof['subject']['path']) == proof['subject'],
             'LEGACY_ACTOR_PROOF_SUBJECT_IN_REGISTRY')
        observed = selected_actors(proof['subject'], proof['selector'])
        need(proof['actors'] == observed and set(observed) <= participants,
             'EXACT_LEGACY_CREATOR_FIELD_SUBSET')
        union.update(observed)
    need(sorted(union) == legacy['legacyActors'] and len(union) == evidence['historicalDeclaredCallers'] == 43,
         'RECOMPUTED_DECLARED_LEGACY_ACTOR_UNION')
    # Conservative review exclusions are preserved as their own evidence. They
    # are not silently reclassified as Source creators or dropped from proofs.
    for proof in legacy['reviewOnlySelectors']:
        need(proof['actors'] == selected_actors(proof['subject'], proof['selector']),
             'EXACT_RETAINED_REVIEW_ONLY_EXCLUSIONS')
    failed_runs = registry['requiredFailedRuns']
    need(type(failed_runs) is list and len(failed_runs) == 14, 'ORIGINAL_FOURTEEN_FAILED_RUN_LINEAGE')
    for row, run_id in zip(declarations[1:15], failed_runs):
        attempt = reader.doc(row['subject'])
        original = registry['failedRunAuthorities'][run_id]
        need(attempt['runId'] == run_id and attempt['registry'] == evidence['historicalRegistry']
             and attempt['originalOutcomeAuthorities'] == original['outcomes']
             and attempt['originalSourceSubject'] == original['sourceSubject'],
             'EXACT_HISTORICAL_ATTEMPT_AUTHORITY_LINEAGE')
        for item in [attempt['originalSourceSubject'], *attempt['originalOutcomeAuthorities'],
                     *attempt['actorEvidenceNodes']]:
            reader.read(item['path'], item)
    need(declarations[15]['subject'] == declarations[16]['subject'], 'SAME_ACTUAL_FIFTEENTH_ATTEMPT_HEADER')
    last = reader.doc(declarations[15]['subject'])
    need(last['runId'] == '3b22101922f48ee4daab728aa77b5d38', 'EXACT_ACTUAL_FIFTEENTH_FAILED_RUN')
    future_pin = declarations[21]['subject']
    need(all(row['subject'] == future_pin for row in declarations[21:]),
         'ONE_SOURCE_BOUND_FUTURE_CALLER_POLICY')
    future = reader.doc(future_pin)
    need(future['actorAuthority'] == authority_pin and future['executionAuthorized'] is False,
         'FUTURE_POLICY_IS_DECLARATION_NOT_RUNTIME_EVIDENCE')
    for selected in (future['futureCandidate'], future['futureHistory'], future['futureSourceControls'],
                     future['futureWindows']['incoming'], future['futureWindows']['archive']):
        need(selected['allowedActors'] == sorted(participants) and selected['operators'] == ['/root'],
             'SOURCE_BOUND_FUTURE_CALLERS_WITHIN_EXACT_FROZEN_ASSIGNMENT')
    return value


def validate_spec(reader, spec, values):
    """Close real selected authority before any output or selector rewrite."""
    closed(spec, SPEC_KEYS, 'CLOSED_COUPLED_ROOT_SPEC')
    need(spec['schema'] == 'e02-root-consumer-coupled-source2-spec-v1'
         and spec['actor'] == '/root', 'ACTUAL_ROOT_COUPLED_SPEC')
    need(spec['rootScope']['sha256'] == SCOPE_SHA
         and spec['rootScope']['path'] == str(SCOPE), 'EXACT_ROOT_SOURCE2_SCOPE')
    reader.doc(spec['rootScope'])
    need(spec['predecessor']['sha256'] == ENTRY_SHA
         and spec['predecessor']['path'] == str(PREDECESSOR / 'entrypoint.UNBOUND.json'),
         'EXACT_REVIEWED_UNBOUND_PREDECESSOR')
    entry = reader.doc(spec['predecessor'])
    need(entry['finalSourceFreezeReady'] is False and entry['canonicalModelsExecuted'] == 0,
         'UNBOUND_IS_NOT_CANONICAL_DATA')
    predecessor_subject = reader.doc(entry['subject'])
    for member in predecessor_subject['sources']:
        reader.read(member['path'], member)
    for field in FINAL.values():
        need(spec[field] is not None, 'MANDATORY_GENUINE_FINAL_SELECTOR:' + field)
        pin_shape(spec[field])
    need(spec['controlClockSelection'] is not None
         and spec['controlClockSelection']['sha256'] == CLOCK_SHA,
         'EXACT_ROOT_FINITE_CONTROL_CLOCK_SELECTION_PIN')
    validate_clock_selection(reader.doc(spec['controlClockSelection']), values['CONTROL_FILES'])
    failed_pin = spec['requiredFailedInventorySelection']
    need(failed_pin is not None and failed_pin['sha256'] == FAILED_SHA,
         'EXACT_ROOT_COMPLETE_FAILED_INVENTORY_SELECTION_PIN')
    failed_policy = reader.doc(failed_pin)
    need(failed_policy['schema'] == 'e02-root-consumer-required-failed-inventory-source-selection-v1'
         and failed_policy['actor'] == '/root'
         and failed_policy['scope'] == 'CURRENT_CONSUMER_RUNTIME_COMPLETE_FAILED_INVENTORY_NO_ROW_DONATION'
         and failed_policy['executionAuthorized'] is False
         and failed_policy['canonicalModelExecutionAuthorized'] is False
         and failed_policy['ordinaryRoleExecutionAuthorized'] is False
         and len(failed_policy['requiredFailedRuns']) == len(set(failed_policy['requiredFailedRuns'])) == 15
         and len(failed_policy['historicalFailures']) == 14,
         'SOURCE_SELECTED_FIFTEEN_FAILURES_NO_RUNTIME_GRANT')
    actors = reader.doc(spec['actorAuthority'])
    closed(actors, ('schema', 'actor', 'participants', 'scope', 'executionAuthorized',
                   'assignment', 'originalHelperFieldDeclarations', 'provenance'),
           'CLOSED_ROOT_ACTOR_AUTHORITY')
    need(actors['schema'] == 'e02-root-consumer-coupled-actor-authority-v1'
         and actors['actor'] == '/root' and actors['executionAuthorized'] is False
         and actors['scope'] == 'FROZEN_FINAL_CONSUMER_SOURCE_AND_MODEL_CALLER_ACTORS_ONLY',
         'ROOT_ACTOR_DECLARATIONS_ONLY')
    members = actors['participants']
    need(type(members) is list and members == sorted(set(members))
         and all(type(v) is str and (v == '/root' or v.startswith('/root/')) for v in members),
         'EXACT_SORTED_DECLARED_ACTORS')
    assignment = actors['assignment']
    closed(assignment, ('sourceOwner', 'operators', 'predecessorSource', 'predecessorActors'),
           'EXACT_FROZEN_CURRENT_ASSIGNMENT')
    need(assignment['sourceOwner'] == AUTHOR and assignment['operators'] == ['/root']
         and assignment['predecessorSource'] == entry['subject']
         and assignment['predecessorActors'] == sorted(values['CURRENT_CONTROL_ACTORS']),
         'AUTHENTICATED_SOURCE1_ACTORS_AND_CURRENT_ASSIGNMENT')
    provenance = actors['provenance']
    closed(provenance, ('actorFieldAttestation', 'assignmentScope', 'method'),
           'EXACT_ACTOR_AUTHORITY_PROVENANCE')
    need(provenance['assignmentScope'] == spec['rootScope']
         and provenance['method'] == 'ACTUAL_ROOT_VERIFIED_TYPED_FIELDS_NOT_OPERATIONAL_BODY_READS'
         and provenance['actorFieldAttestation']['sha256'] ==
         '3c3669d4661461cc8ca69686e5aa7bafdaf4f6bb49ea375a0d29c005dab9aa7a',
         'EXACT_ROOT_MEMORY_ACTOR_ATTESTATION')
    attestation = reader.doc(provenance['actorFieldAttestation'])
    need(attestation['actor'] == '/root' and attestation['executionAuthorized'] is False
         and attestation['schema'] == 'e02-root-original-helper-actor-field-attestation-v1'
         and actors['originalHelperFieldDeclarations'] == attestation['fieldDeclarations'],
         'ORIGINAL_HELPER_FIELDS_FROM_ACTUAL_ROOT_ATTESTATION')
    original_root = reader.doc(attestation['originalHelperAcceptance'])
    need(len(attestation['fieldDeclarations']) == 2, 'EXACT_HELPER_SUBJECT_AND_RELEASE_DECLARATIONS')
    expected_originals = {original_root['subject']['path']: original_root['subject'],
                          original_root['rootRelease']['path']: original_root['rootRelease']}
    observed_originals = set()
    union = set(values['CURRENT_CONTROL_ACTORS']) | {AUTHOR, '/root'}
    predecessor = reader.doc(entry['subject'])
    union.update(predecessor['sourceContributors'])
    for key in ('author', 'coordinator', 'predecessorAuthor'):
        union.add(predecessor[key])
    union.update(predecessor.get('operators', []))
    for row in attestation['fieldDeclarations']:
        original = row['originalRecord']  # Opaque descriptor; NEVER read it.
        need(expected_originals.get(original['path']) == original,
             'ORIGINAL_HELPER_ROOT24_FIELD_JOIN')
        observed_originals.add(original['path'])
        for field in ('authors', 'operators'):
            need(type(row[field]) is list and row[field]
                 and all(type(v) is str and (v == '/root' or v.startswith('/root/')) for v in row[field]),
                 'AUTHENTICATED_NONEMPTY_ORIGINAL_HELPER_ACTORS')
            union.update(row[field])
    need(observed_originals == set(expected_originals) and members == sorted(union),
         'EXACT_COMPLETE_FROZEN_CALLER_ACTOR_UNION')
    forbidden = set(members)
    validate_caller_closure(reader, spec['callerClosure'], spec['callerClosureEvidence'], spec['actorAuthority'], forbidden)
    source = reader.doc(values['CURRENT_PRODUCER'])
    source_ack = reader.doc(values['CURRENT_PRODUCER_SOURCE_ACCEPTANCE'])
    need(source_ack['subject'] == values['CURRENT_PRODUCER']
         and source_ack['decision'] == 'ACCEPT_PRODUCER_EOSE_SOURCE_AND_286_DEFINITIONS_ONLY',
         'GENUINE_CURRENT_PRODUCER_SOURCE_ACCEPTANCE')
    reviews(reader, source_ack['reviews'], values['CURRENT_PRODUCER'], source_ack['decision'], forbidden)
    capture = reader.doc(spec['captureSource'])
    capture_ack = reader.doc(spec['captureSourceAcceptance'])
    need(capture['producerSource'] == values['CURRENT_PRODUCER']
         and capture['codeOnly'] is True and capture_ack['subject'] == spec['captureSource']
         and capture_ack['decision'] == 'ACCEPT_PRODUCER4_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY'
         and capture_ack['executionAuthorized'] is False, 'GENUINE_CURRENT_CAPTURE_SOURCE')
    reviews(reader, capture_ack['reviews'], spec['captureSource'], capture_ack['decision'], forbidden)
    admission = reader.doc(spec['admissionDataAcceptance'])
    admission_data = reader.doc(admission['subject'])
    n = capture['admissionModelsDefined']
    need(type(n) is int and n > 0 and admission['captureSource'] == spec['captureSource']
         and admission['producerSource'] == values['CURRENT_PRODUCER']
         and admission['decision'] == 'ACCEPT_PRODUCER4_CAPTURE_ADMISSION_DATA_ONLY'
         and admission['executionAuthorized'] is False, 'GENUINE_CURRENT_ADMISSION_ACCEPTANCE')
    for key in ('modelsDefined', 'modelsExecuted', 'modelsPassed'):
        need(type(admission[key]) is int and admission[key] == n
             and type(admission_data[key]) is int and admission_data[key] == n,
             'ALL_ADMISSION_DEFINITIONS_EXECUTED')
    need(admission_data['inputsUnchanged'] is True and admission_data['truncated'] is False
         and admission_data['skipped'] == 0 and admission_data['modelsFailed'] == 0,
         'COMPLETE_ADMISSION_DATA_ONLY')
    reviews(reader, admission['reviews'], admission['subject'], admission['decision'], forbidden)
    control = reader.doc(spec['producerControlData'])
    control_ack = reader.doc(spec['producerControlAcceptance'])
    rule = reader.doc(values['CURRENT_DATA_ACCEPTANCE_CONTRACT'])
    closed(control_ack, rule['closedKeys'], 'CLOSED_CURRENT286_ROOT_DATA_ACCEPTANCE')
    for key, expected in rule['literals'].items():
        need(type(control_ack[key]) is type(expected) and control_ack[key] == expected,
             'EXACT_CURRENT286_ROOT_LITERAL:' + key)
    need(control_ack['subject'] == spec['producerControlData'], 'EXACT_CURRENT286_DATA_SUBJECT')
    joins = dict(producerSource=values['CURRENT_PRODUCER'],
        producerSourceAcceptance=values['CURRENT_PRODUCER_SOURCE_ACCEPTANCE'],
        captureSource=spec['captureSource'], captureSourceAcceptance=spec['captureSourceAcceptance'],
        admissionDataAcceptance=spec['admissionDataAcceptance'], countsSeparate=COUNTS)
    for key, expected in joins.items():
        need(control[key] == expected and control_ack[key] == expected,
             'CURRENT286_SOURCE_DATA_ROOT_JOIN:' + key)
    need(control['allExpectedInputsUnchanged'] is True and control['runtimeAuthorized'] is False,
         'UNCHANGED_CURRENT286_PURE_DATA_ONLY')
    reviews(reader, control_ack['reviews'], spec['producerControlData'],
            rule['literals']['decision'], forbidden)
    template = reader.doc(values['CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE'])
    basis = reader.doc(spec['helperComponentBasis'])
    closed(basis, template, 'CLOSED_COMPLETED_COMPONENT_BASIS')
    for key in ('actor', 'schema', 'scope', 'contract', 'designAuthor', 'originalBasis'):
        need(basis[key] == template[key], 'IMMUTABLE_ORIGINAL_HELPER_BASIS:' + key)
    need(basis['issued'] is True and basis['readiness'] is True
         and basis['executionAuthorized'] is False
         and basis['state'] == 'COMPLETED_SOURCE_COMPONENT_BASIS_ONLY',
         'ACTUAL_COMPLETED_SOURCE_COMPONENT_BASIS_REQUIRED')
    ordinary = dict(joins, controlPlan=source['controlPlan'], modelsDefined=286,
        producerControlData=spec['producerControlData'],
        producerControlAcceptance=spec['producerControlAcceptance'])
    need(basis['ordinarySuccessor'] == ordinary, 'BASIS_EXACT_ACTUAL_NEW286_TUPLE')
    need(set(members) <= set(basis['actorClosure']['participants']), 'BASIS_COVERS_FINAL_CALLER_SET')
    design = reader.doc(values['CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE'])
    need(basis['sourceReviews'] == design['reviews']
         and basis['rootDisposition'] == values['CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE'],
         'PRIOR_DESIGN_AUTHORITY_NO_BASIS_SELF_ACCEPTANCE')
    evidence = spec['basisVerificationEvidence']
    need(type(evidence) is list and evidence, 'EXTERNAL_COMPLETED_SOURCE_MAPPING_VERIFICATION')
    for pin in evidence:
        reader.doc(pin)
    return members, basis, template, ordinary


class Closure:
    """Finite typed read-site closure; no recursive descriptor discovery."""
    def __init__(self, reader):
        self.reader = reader
        self.rows = {}
        self.uses = {}
        self.opaque = {}

    def add(self, pin, selector, kind='SOURCE_OR_GOVERNANCE'):
        pin_shape(pin)
        old = self.rows.get(pin['path'])
        need(old is None or old == pin, 'NO_EXPECTED_PIN_SUBSTITUTION')
        opaque = self.opaque.get(pin['path'])
        if opaque is None:
            self.reader.read(pin['path'], pin)
        else:
            need(opaque == pin, 'EXACT_ROOT_OPAQUE_HISTORICAL_NEGATIVE_PIN')
            kind = 'HISTORICAL_NEGATIVE_OPERATIONAL_OPAQUE'
        self.rows[pin['path']] = pin
        self.uses.setdefault(pin['path'], []).append(dict(selector=selector, kind=kind,
            physicalReadDuringSource=opaque is None))

    def doc(self, pin, selector, kind='PURE_CONTROL_METADATA'):
        self.add(pin, selector, kind)
        return self.reader.doc(pin)

    def fields(self, doc, names, selector, kind='PURE_CONTROL_METADATA'):
        for key in names:
            self.add(doc[key], selector + '/' + key, kind)

    def pair(self, acceptance, selector):
        for index, pin in enumerate(acceptance['reviews']):
            self.add(pin, selector + '/reviews/' + str(index), 'GOVERNANCE')

    def manifest(self, pin, selector):
        value = self.doc(pin, selector)
        need(type(value['files']) is list, 'FINITE_PURE_CONTROL_RAW_FILES')
        for index, item in enumerate(value['files']):
            self.add(item, selector + '/files/' + str(index), 'PURE_CONTROL_RAW')
        for field in ('runtimeManifest', 'originalToolOrigin'):
            if value.get(field) is not None:
                self.add(value[field], selector + '/' + field, 'PURE_CONTROL_RAW')

    def control(self, subject_pin, root_pin, selector, family='producer'):
        data = self.doc(subject_pin, selector + '/subject')
        ack = self.doc(root_pin, selector + '/acceptance', 'GOVERNANCE')
        self.pair(ack, selector + '/acceptance')
        fields = {
            'producer': ('execution', 'originalToolOrigin', 'rawArtifactManifest'),
            'helperMethod': ('helperSource', 'helperSourceAcceptance', 'controlPlan', 'job',
                'rootRelease', 'originalToolOrigin', 'rawOutput', 'rawArtifactManifest',
                'sourceAcceptedMetadataValidator'),
            'controller': ('controllerSource', 'controllerSourceAcceptance', 'controlPlan',
                'rootRelease', 'execution', 'rawArtifactManifest')}
        schemas = {'producer': 'e02-producer4-current-control-data-subject-v1',
                   'helperMethod': 'e02-helper-current178-control-data-subject-v1',
                   'controller': 'e02-probe-controller-mock-control-data-subject-v1'}
        need(family in fields and data['schema'] == schemas[family], 'EXPLICIT_PURE_CONTROL_FAMILY')
        self.fields(data, fields[family], selector + '/subject')
        if family == 'controller':
            for index, pin in enumerate(data['originalToolOrigins']):
                self.add(pin, selector + '/originalToolOrigins/' + str(index), 'PURE_CONTROL_RAW')
        self.manifest(data['rawArtifactManifest'], selector + '/rawArtifactManifest')
        for field in ('inputsBefore', 'inputsAfter'):
            if field in data:
                self.add(data[field], selector + '/subject/' + field, 'PURE_CONTROL_RAW')
        if 'rootAcknowledgement' in data:
            grant = self.doc(data['rootAcknowledgement'], selector + '/rootAcknowledgement')
            self.fields(grant, ('producerSource', 'producerSourceAcceptance', 'captureSource',
                'captureSourceAcceptance', 'admissionPlan', 'admissionData', 'admissionDataAcceptance',
                'sourceBirth', 'actorContext', 'inputManifest', 'plan', 'clockSelection',
                'requestContract', 'runtimeBindings'), selector + '/rootAcknowledgement')
            for family in ('producerReviews', 'captureReviews', 'admissionReviews'):
                for index, pin in enumerate(grant[family]):
                    self.add(pin, selector + '/rootAcknowledgement/' + family + '/' + str(index), 'GOVERNANCE')
            context = self.reader.doc(grant['actorContext'])
            for index, proof in enumerate(context['participantProofs']):
                self.add(proof['authority'], selector + '/actorContext/participantProofs/' + str(index) + '/authority')
            admission = self.reader.doc(grant['admissionData'])
            self.fields(admission, ('execution', 'originalToolOrigin', 'rawArtifactManifest',
                'inputsBefore', 'inputsAfter'), selector + '/admissionData')
            self.manifest(admission['rawArtifactManifest'], selector + '/admissionRaw')
        return data, ack


def fixed_closure(reader, spec, values, basis, template):
    result = Closure(reader)
    opaque_pin = spec['historicalNegativeInputAuthority']
    need(opaque_pin is not None and opaque_pin['sha256'] == OPAQUE_SHA,
         'EXACT_ROOT_OPAQUE_HISTORICAL_NEGATIVE_SOURCE_DECISION')
    decision = result.doc(opaque_pin, 'rootHistoricalNegativeInputAuthority', 'GOVERNANCE')
    need(decision['actor'] == '/root'
         and decision['decision'] == 'PRESERVE_TWO_HISTORICAL_NEGATIVE_EXPECTED_ROWS_OPAQUE_DURING_SOURCE_PREPARATION'
         and decision['sourceReadmapRole'] == 'HISTORICAL_NEGATIVE_OPERATIONAL_OPAQUE'
         and decision['sourceOnly'] is True
         and decision['physicalHistoricalBodyReadsAuthorized'] is False
         and decision['current65BodyReadsAuthorized'] is False
         and decision['canonicalModelExecutionAuthorized'] is False
         and decision['executionAuthorized'] is False, 'OPAQUE_SOURCE_TREATMENT_HAS_NO_BODY_READ_AUTHORITY')
    need(type(decision['opaqueRows']) is list and len(decision['opaqueRows']) == 2,
         'EXACT_TWO_ROOT_OPAQUE_OPERANDS')
    result.opaque = {pin['path']: pin for pin in decision['opaqueRows']}
    need(len(result.opaque) == 2, 'NO_OPAQUE_OPERAND_ALIAS')
    historical_pin, _ = reader.read(PREDECESSOR / 'baseline-metadata/input-manifest.json')
    historical = result.doc(historical_pin, 'preservedBaseline/inputManifest')
    need(historical_pin == decision['baselineManifest']
         and len(historical['fixedSourceAndCurrentDataOperands']) == decision['baselineExpectedRows'] == 847,
         'ALL_AUTHENTICATED_BASELINE_EXPECTED_ROWS_PRESERVED')
    for index, pin in enumerate(historical['fixedSourceAndCurrentDataOperands']):
        result.add(pin, 'preservedBaseline/fixedSourceAndCurrentDataOperands/' + str(index),
                   'EXPLICIT_HISTORICAL_SOURCE_OR_PURE_CONTROL')
    predecessor_entry = result.doc(spec['predecessor'], 'predecessor/entrypoint', 'SOURCE')
    predecessor_source = result.doc(predecessor_entry['subject'], 'predecessor/subject', 'SOURCE')
    result.add(predecessor_entry['archive'], 'predecessor/sourceArchive', 'SOURCE')
    preservation = result.doc(predecessor_entry['preservation'], 'predecessor/preservation', 'SOURCE')
    for index, row in enumerate(preservation['rows']):
        if row.get('baseline') is not None:
            result.add(row['baseline'], 'predecessor/preservation/rows/' + str(index) + '/baseline', 'SOURCE')
    for index, pin in enumerate(predecessor_source['sources']):
        result.add(pin, 'predecessor/sources/' + str(index), 'SOURCE')
    for path, pin in BOOTSTRAP_EXPECTED.items():
        if Path(path).is_relative_to(PREDECESSOR):
            result.add(pin, 'immutablePredecessorPackage/' + str(Path(path).relative_to(PREDECESSOR)),
                       'SOURCE')
    for key, value in spec.items():
        if key in ('basisVerificationEvidence', 'inputFiles'):
            for index, pin in enumerate(value):
                result.add(pin, 'rootSpec/' + key + '/' + str(index), 'SOURCE_MAPPING_VERIFICATION')
        elif type(value) is dict:
            result.add(value, 'rootSpec/' + key)
    if spec.get('callerClosure') is not None:
        caller = result.doc(spec['callerClosure'], 'rootCallerClosure', 'GOVERNANCE')
        evidence = result.doc(spec['callerClosureEvidence'], 'rootCallerClosure/evidence', 'GOVERNANCE')
        for index, row in enumerate(caller['declarations']):
            result.add(row['subject'], 'rootCallerClosure/declarations/' + str(index) + '/subject',
                       'GOVERNANCE_CALLER_METADATA')
        for index, pin in enumerate(evidence['inputs']):
            result.add(pin, 'rootCallerClosure/evidence/inputs/' + str(index), 'GOVERNANCE_CALLER_METADATA')
        for field in ('priorPreparationEvidence', 'priorCallerClosure', 'historicalRegistry'):
            result.add(evidence[field], 'rootCallerClosure/evidence/' + field, 'GOVERNANCE')
        legacy = reader.doc(caller['declarations'][0]['subject'])
        for index, pin in enumerate(legacy['finiteNodes']):
            result.add(pin, 'rootCallerClosure/legacy/finiteNodes/' + str(index), 'GOVERNANCE_CALLER_METADATA')
        for index, row in enumerate(caller['declarations'][1:15]):
            attempt = reader.doc(row['subject'])
            result.add(attempt['originalSourceSubject'], 'rootCallerClosure/attempt/' + str(index) + '/originalSourceSubject', 'SOURCE')
            for field in ('originalOutcomeAuthorities', 'actorEvidenceNodes'):
                for n, pin in enumerate(attempt[field]):
                    result.add(pin, 'rootCallerClosure/attempt/' + str(index) + '/' + field + '/' + str(n),
                               'GOVERNANCE_CALLER_METADATA')
    if spec.get('requiredFailedInventorySelection') is not None:
        failed = result.doc(spec['requiredFailedInventorySelection'], 'requiredFailedInventorySelection', 'GOVERNANCE')
        result.add(failed['historicalRegistry'], 'requiredFailedInventorySelection/historicalRegistry', 'GOVERNANCE')
        for index, row in enumerate(failed['historicalFailures']):
            result.add(row['sourceSubject'], 'requiredFailedInventory/historical/' + str(index) + '/sourceSubject', 'SOURCE')
            for number, pin in enumerate(row['allowedRawOutcomes']):
                result.add(pin, 'requiredFailedInventory/historical/' + str(index) + '/allowedRawOutcomes/' + str(number),
                           'GOVERNANCE_CALLER_METADATA')
        result.fields(failed['currentFailure'], ('subject', 'rootNegativeDisposition'),
                      'requiredFailedInventory/currentFailure', 'GOVERNANCE')
    # Source-level literal descriptors have a finite authenticated AST namespace.
    # Binary APK/native payload operands remain opaque declarations, not reads.
    excluded = {'CURRENT_AMETHYST_APK', 'CURRENT_HELPER_APK', 'CURRENT_NATIVE'}
    for name, value in values.items():
        if name.startswith(('CURRENT_', 'HISTORICAL_', 'HELPER_')) and name not in excluded \
                and type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}:
            result.add(value, 'consumer.py/' + name)
    for label, pin in (('ordinarySource', values['CURRENT_PRODUCER']),
                       ('originalHelperSource', values['HELPER_PRODUCER'])):
        source = result.doc(pin, label)
        for field in ('sources', 'runtimeSources', 'externalControlSources'):
            for index, member in enumerate(source.get(field, [])):
                result.add(member, label + '/' + field + '/' + str(index), 'SOURCE')
        result.fields(source, ('controlPlan',), label, 'SOURCE')
        for role, config in source['configurations'].items():
            result.add(config, label + '/configurations/' + role, 'SOURCE')
    result.control(spec['producerControlData'], spec['producerControlAcceptance'], 'ordinary286')
    old = basis['originalBasis']
    original = old['producer']
    result.control(original['producerData'], original['producerDataAcceptance'], 'original266')
    for label, pin in (('ordinaryCapture', spec['captureSource']),
                       ('originalCapture', original['producerCaptureSource'])):
        capture = result.doc(pin, label)
        for index, source in enumerate(capture['sources']):
            result.add(source, label + '/sources/' + str(index), 'SOURCE')
    # These are pure mock-control authorities, NOT the accepted actual helper.
    for label, source_key, acceptance_key in (
        ('helperMethod', 'helperMethodSource', 'helperMethodControlAcceptance'),
        ('controller', None, None)):
        if label == 'controller':
            source_pin = old['controller']['controllerSource']
            root_pin = old['controller']['controllerControlDataAcceptance']
        else:
            source_pin, root_pin = old[source_key], old[acceptance_key]
        source = result.doc(source_pin, label + '/source', 'SOURCE')
        member_key = 'sourceInputs' if label == 'helperMethod' else 'sources'
        expected_schema = ('e02-helper-current178-source-subject-v1' if label == 'helperMethod'
                           else 'e02-one-cid-helper-probe-controller-source-v1')
        need(source['schema'] == expected_schema, 'EXACT_TYPED_HELPER_OR_CONTROLLER_SOURCE')
        for index, source_member in enumerate(source[member_key]):
            result.add(source_member, label + '/source/' + member_key + '/' + str(index),
                       'EXPLICIT_SOURCE_OR_PURE_CONTROL')
        root = result.doc(root_pin, label + '/controlAcceptance', 'GOVERNANCE')
        result.control(root['subject'], root_pin, label + '/pureControls', label)
    # Only Root24 and its two closed governance decisions are read. Its S18,
    # plan/release/result/M4/Host/F children are intentionally opaque operands.
    helper_root = result.doc(old['helperDataAcceptance'], 'originalHelper/Root24', 'GOVERNANCE')
    result.pair(helper_root, 'originalHelper/Root24')
    authority = reader.doc(spec['actorAuthority'])
    attestation_pin = authority['provenance']['actorFieldAttestation']
    attestation = result.doc(attestation_pin, 'actorAuthority/provenance/actorFieldAttestation', 'GOVERNANCE')
    result.add(attestation['closureDescriptor'], 'originalHelper/finalClosureDescriptor', 'GOVERNANCE')
    for index, pair in enumerate(basis['sourcePairs']):
        for field in ('originalPin', 'newPin'):
            result.add(pair[field], 'completedBasis/sourcePairs/' + str(index) + '/' + field,
                       'HELPER_COMPONENT_SOURCE')
            reader.read(pair[field]['path'], pair[field], 0o664)
    boundary = old['boundary']
    result.fields(boundary, ('controllerConstants', 'guardManifest'), 'originalBoundary', 'SOURCE')
    for index, pin in enumerate(boundary['controllerRuntimeSources']):
        result.add(pin, 'originalBoundary/controllerRuntimeSources/' + str(index), 'SOURCE')
    design = result.doc(values['CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE'], 'componentDesign', 'GOVERNANCE')
    result.add(design['subject'], 'componentDesign/subject', 'SOURCE')
    result.pair(design, 'componentDesign')
    return result


def rewrite_assignments(body, replacements):
    lines = body.decode('utf8').splitlines(True)
    changes = []
    found = set()
    for node in ast.parse(body).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in replacements:
                changes.append((node.lineno - 1, node.end_lineno, name + ' = ' + repr(replacements[name]) + '\n'))
                found.add(name)
    need(found == set(replacements), 'EXACT_ASSIGNMENT_REWRITE_SET')
    for start, stop, replacement in sorted(changes, reverse=True):
        lines[start:stop] = [replacement]
    result = ''.join(lines).encode()
    ast.parse(result)
    return result


def adapt_request_fixture(body):
    """Two reviewed current-fixture corrections; same methods and validators."""
    lines = body.decode('utf8').splitlines(True)
    selected = {
        'test_current_accepted_r10_178_model_data_is_consumed_without_activation':
            ('consumer.CURRENT_PRODUCER, consumer.CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT',
             'consumer.HELPER_PRODUCER, consumer.CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT'),
        'test_actual_current_producer_reader_binds_ab6_native4ce_and_fresh_e01':
            ("'CURRENT_ACCEPTED_ARTIFACT_BINDINGS_R1'", "'FIXTURE_EOSE_QUEUE_CALLER_R1'")}
    changes = []
    for cls in ast.parse(body).body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for method in cls.body:
            if isinstance(method, ast.FunctionDef) and method.name in selected:
                before = ''.join(lines[method.lineno - 1:method.end_lineno])
                old, new = selected[method.name]
                need(before.count(old) == 1, 'EXACT_AUTHORIZED_REQUEST_FIXTURE_ADAPTATION')
                changes.append((method.lineno - 1, method.end_lineno, before.replace(old, new)))
    need(len(changes) == len(selected), 'BOTH_DIAGNOSED_FIXTURES_RETAINED')
    for start, end, replacement in sorted(changes, reverse=True):
        lines[start:end] = [replacement]
    return ''.join(lines).encode()


def install_clock_source(body, clock_pin, clock_record, control_names):
    """Only the separately Root-selected pure model request clock changes."""
    clocks = validate_clock_selection(clock_record, control_names)
    text = body.decode()
    marker = '_ACTIVE_BINDINGS = None\n'
    need(text.count(marker) == 1, 'ONE_CURRENT_BINDING_DECLARATION')
    declarations = ('CURRENT_CONSUMER_CONTROL_CLOCK_SELECTION = ' + repr(clock_pin) + '\n'
        + 'CURRENT_CONTROL_CLOCK_SELECTION_RECORD = ' + repr(clock_record) + '\n'
        + 'CURRENT_CONTROL_SCOPE_SECONDS = ' + repr(clocks) + '\n\n')
    text = text.replace(marker, declarations + marker)
    tree = ast.parse(text)
    old = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == 'current_control_request')
    lines = text.splitlines(True)
    replacement = '''def control_clock_map(selection):
    """Validate the exact Source-selected finite pure-control clock semantics."""
    closed(selection, 'schema actor scope predecessorControlPlan selection groups totalSerialOuterKillSeconds basis sourceRequirements helperAndControllerR10ClocksChanged ordinaryLeaseSeconds ordinaryClockChanged producer286ClockChanged modelExecutionAuthorized executionAuthorized')
    equal(selection['schema'], 'e02-root-consumer-pure-control-clock-source-selection-v1')
    equal(selection['actor'], '/root')
    equal(selection['scope'], 'CURRENT_COUPLED_CONSUMER_PURE_CONTROL_REQUESTS_ONLY')
    equal(selection['selection'], 'FIXED_PER_GROUP_OUTER_KILL_BOUND_WITHOUT_RENEWAL')
    for name in ('executionAuthorized', 'modelExecutionAuthorized', 'helperAndControllerR10ClocksChanged', 'ordinaryClockChanged', 'producer286ClockChanged'):
        equal(selection[name], False, 'ROOT_PURE_CLOCK_SELECTION_HAS_NO_RUNTIME_AUTHORITY')
    equal(selection['ordinaryLeaseSeconds'], 1800)
    pin_shape(selection['predecessorControlPlan'])
    groups = selection['groups']
    need(type(groups) is list, 'ROOT_CONTROL_CLOCK_GROUPS')
    equal([g['name'] for g in groups], list(CONTROL_FILES), 'ALL_THIRTEEN_ROOT_CONTROL_CLOCK_NAMES')
    equal(len(groups), 13);equal(len({g['name'] for g in groups}), 13)
    result = {}
    for group in groups:
        closed(group, 'name definitions outerKillSeconds')
        integer(group['definitions'], 1)
        seconds = 120 if group['name'] == 'test_current_authority.py' else 63
        equal(group['outerKillSeconds'], seconds, 'EXACT_NAME_SELECTED_FINITE_CONTROL_CLOCK')
        result[group['name']] = seconds
    equal(selection['totalSerialOuterKillSeconds'], sum(result.values()))
    equal(selection['totalSerialOuterKillSeconds'], 876)
    return result


def current_control_request(group):
    import shlex
    clocks = control_clock_map(CURRENT_CONTROL_CLOCK_SELECTION_RECORD)
    equal(clocks, CURRENT_CONTROL_SCOPE_SECONDS, 'SOURCE_PINNED_ROOT_CLOCK_MAP')
    need(group['name'] in clocks, 'UNKNOWN_CONTROL_CLOCK_GROUP')
    argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',
        '/usr/bin/timeout','--signal=KILL',str(clocks[group['name']])+'s',*group['argv']]
    return dict(cmd=shlex.join(argv),workdir=group['cwd'],login=False,yield_time_ms=1000,max_output_tokens=20000)
'''
    lines[old.lineno - 1:old.end_lineno] = [replacement]
    return ''.join(lines).encode()


def add_clock_controls(body):
    text = body.decode()
    marker = "if __name__=='__main__':unittest.main()"
    need(text.count(marker) == 1, 'ONE_SOURCE_BINDING_TEST_MAIN')
    methods = '''    def test_root_selected_authority_clock_is120_seconds_once(self):
        pin=consumer.CURRENT_CONSUMER_CONTROL_CLOCK_SELECTION
        raw=Path(pin['path']).read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(pin['bytes'],pin['sha256']))
        selected=json.loads(raw)
        self.assertEqual(consumer.control_clock_map(selected),consumer.CURRENT_CONTROL_SCOPE_SECONDS)
        group=dict(name='test_current_authority.py',argv=['/synthetic/python','-v'],cwd='/synthetic')
        self.assertIn('--signal=KILL 120s',consumer.current_control_request(group)['cmd'])

    def test_other_twelve_pure_group_clocks_remain63_seconds(self):
        for name in consumer.CONTROL_FILES:
            if name!='test_current_authority.py':
                group=dict(name=name,argv=['/synthetic/python','-v'],cwd='/synthetic')
                self.assertIn('--signal=KILL 63s',consumer.current_control_request(group)['cmd'])
        self.assertEqual(sum(consumer.CURRENT_CONTROL_SCOPE_SECONDS.values()),876)

    def test_clock_metadata_duplicates_omissions_substitution_and_authority_refused(self):
        original=consumer.CURRENT_CONTROL_CLOCK_SELECTION_RECORD
        candidates=[]
        value=json.loads(json.dumps(original));value['groups'][1]=value['groups'][0];candidates.append(value)
        value=json.loads(json.dumps(original));value['groups'].pop();candidates.append(value)
        value=json.loads(json.dumps(original));value['groups'][0]['outerKillSeconds']=120;candidates.append(value)
        value=json.loads(json.dumps(original));value['groups'][8]['outerKillSeconds']=63;candidates.append(value)
        value=json.loads(json.dumps(original));value['executionAuthorized']=True;candidates.append(value)
        value=json.loads(json.dumps(original));value['modelExecutionAuthorized']=True;candidates.append(value)
        for value in candidates:
            with self.assertRaises(Refusal):consumer.control_clock_map(value)

    def test_unknown_control_group_cannot_inherit_another_clock(self):
        with self.assertRaisesRegex(Refusal,'UNKNOWN_CONTROL_CLOCK_GROUP'):
            consumer.current_control_request(dict(name='unknown.py',argv=[],cwd='/synthetic'))

'''
    return text.replace(marker, methods + marker).encode()


def install_failed_inventory_source(body, pin, policy):
    """Add the Root-selected runtime gate without changing generic provenance."""
    text = body.decode()
    marker = '_ACTIVE_BINDINGS = None\n'
    need(text.count(marker) == 1, 'ONE_SOURCE_RUNTIME_BINDING_DECLARATION')
    declarations = ('CURRENT_REQUIRED_FAILED_INVENTORY_SELECTION = ' + repr(pin) + '\n'
        + 'CURRENT_REQUIRED_FAILED_INVENTORY_RECORD = ' + repr(policy) + '\n\n')
    text = text.replace(marker, declarations + marker)
    function = '''def require_failed_inventory(attempt_docs):
    """Complete fixed failed-run history before any contributing window/control."""
    policy = CURRENT_REQUIRED_FAILED_INVENTORY_RECORD
    equal(policy['schema'], 'e02-root-consumer-required-failed-inventory-source-selection-v1')
    equal(policy['actor'], '/root')
    equal(policy['scope'], 'CURRENT_CONSUMER_RUNTIME_COMPLETE_FAILED_INVENTORY_NO_ROW_DONATION')
    for name in ('executionAuthorized', 'canonicalModelExecutionAuthorized', 'ordinaryRoleExecutionAuthorized'):
        equal(policy[name], False)
    required = policy['requiredFailedRuns']
    equal(len(required), 15);equal(len(set(required)), 15)
    need(type(attempt_docs) is list, 'WHOLE_PARSED_ATTEMPT_INVENTORY')
    indexed = {}
    for row, attempt in attempt_docs:
        run_id = attempt['runId']
        need(run_id not in indexed, 'DUPLICATE_HISTORY_RUNID')
        indexed[run_id] = (row, attempt)
    for run_id in required:
        need(run_id in indexed, 'MISSING_REQUIRED_FAILED_RUN:' + run_id)
        row, attempt = indexed[run_id]
        equal(row['disposition'], 'NO_CONTRIBUTION', 'REQUIRED_FAILED_RUN_CANNOT_DONATE')
        equal(attempt['windowSubject'], None, 'REQUIRED_FAILED_RUN_CANNOT_DONATE_WINDOW')
        equal(row['classification'], attempt['outcomeClassification'])
    historical = policy['historicalFailures']
    equal([item['runId'] for item in historical], required[:-1])
    for item in historical:
        _, attempt = indexed[item['runId']]
        equal(attempt['sourceSubject'], item['sourceSubject'], 'EXACT_HISTORICAL_FAILED_SOURCE')
        need(any(same(attempt['rawOutcome'], allowed) for allowed in item['allowedRawOutcomes']),
             'EXACT_HISTORICAL_FAILED_RAW_OUTCOME')
    current = policy['currentFailure']
    row, attempt = indexed[required[-1]]
    equal(row['subject'], current['subject'], 'EXACT_ACTUAL_FIFTEENTH_ATTEMPT_PIN')
    equal(attempt, current['expectedSubject'], 'EXACT_ACTUAL_FIFTEENTH_ATTEMPT_BODY')
    return attempt_docs


'''
    marker = 'def provenance(files, candidate, history, origin_value):\n'
    need(text.count(marker) == 1, 'ONE_UNCHANGED_GENERIC_PROVENANCE_FUNCTION')
    text = text.replace(marker, function + marker)
    call = '    forbidden, attempts = provenance(files, candidate, history, origin_value)\n'
    need(text.count(call) == 1, 'ONE_ACTUAL_CONSUME_PROVENANCE_CALL')
    return text.replace(call, call + '    require_failed_inventory(attempts)\n').encode()


def add_failed_inventory_controls(body):
    text = body.decode()
    marker = "if __name__ == '__main__':\n    unittest.main(verbosity=2)"
    need(text.count(marker) == 1, 'ONE_DATA_CONTROL_TEST_MAIN')
    controls = '''class RequiredFailedInventoryControls(unittest.TestCase):
    def rows(self):
        policy=consumer.CURRENT_REQUIRED_FAILED_INVENTORY_RECORD
        rows=[]
        for item in policy['historicalFailures']:
            run=item['runId']
            attempt=dict(schema='e02-minimum-attempt-subject-v1',profileId=wire.PROFILE,
                attemptId='SYNTHETIC-'+run,ordinaryRole='incoming',runId=run,windowSubject=None,
                rawOutcome=copy.deepcopy(item['allowedRawOutcomes'][0]),authors=['/root'],operators=['/root'],
                sourceSubject=copy.deepcopy(item['sourceSubject']),outcomeClassification='FAILED_UNQUALIFIED')
            row=dict(subject=dict(path='/model/SYNTHETIC-'+run,bytes=1,sha256='a'*64),
                disposition='NO_CONTRIBUTION',classification=attempt['outcomeClassification'],reason='Synthetic predicate fixture only')
            rows.append((row,attempt))
        current=policy['currentFailure']
        rows.append((dict(subject=copy.deepcopy(current['subject']),disposition='NO_CONTRIBUTION',
            classification=current['expectedSubject']['outcomeClassification'],reason='Root-selected metadata copied into memory fixture'),
            copy.deepcopy(current['expectedSubject'])))
        for run in ('e'*32,'f'*32):
            rows.append((dict(subject=dict(path='/model/SYNTHETIC-FRESH-'+run,bytes=1,sha256='b'*64),
                disposition='CONTRIBUTE_WHOLE_WINDOW',classification='COMPLETE_PENDING_INDEPENDENT_QUALIFICATION',reason='Synthetic fresh contributor'),
                dict(runId=run,windowSubject=dict(path='/model/SYNTHETIC-WINDOW-'+run,bytes=1,sha256='c'*64))))
        return rows

    def test_all_fifteen_failures_and_two_fresh_contributors_are_retained(self):
        rows=self.rows();self.assertIs(consumer.require_failed_inventory(rows),rows)
        self.assertEqual(len(rows),17)

    def test_missing_actual_fifteenth_failure_cannot_be_replaced_by_fresh_windows(self):
        rows=self.rows();del rows[14]
        with self.assertRaisesRegex(strict.Refusal,'MISSING_REQUIRED_FAILED_RUN'):
            consumer.require_failed_inventory(rows)

    def test_missing_any_original_failed_run_is_refused(self):
        rows=self.rows();del rows[0]
        with self.assertRaisesRegex(strict.Refusal,'MISSING_REQUIRED_FAILED_RUN'):
            consumer.require_failed_inventory(rows)

    def test_duplicate_run_id_with_a_new_attempt_id_is_refused(self):
        rows=self.rows();duplicate=copy.deepcopy(rows[0]);duplicate[1]['attemptId']='SYNTHETIC-DIFFERENT-ATTEMPT-ID';rows.append(duplicate)
        with self.assertRaisesRegex(strict.Refusal,'DUPLICATE_HISTORY_RUNID'):
            consumer.require_failed_inventory(rows)

    def test_required_failed_run_relabel_or_window_donation_is_refused(self):
        for index in (0,14):
            rows=self.rows();rows[index][0]['disposition']='CONTRIBUTE_WHOLE_WINDOW'
            with self.assertRaisesRegex(strict.Refusal,'REQUIRED_FAILED_RUN_CANNOT_DONATE'):
                consumer.require_failed_inventory(rows)
            rows=self.rows();rows[index][1]['windowSubject']=dict(path='/model/NOT-A-QUALIFIED-WINDOW',bytes=1,sha256='d'*64)
            with self.assertRaisesRegex(strict.Refusal,'REQUIRED_FAILED_RUN_CANNOT_DONATE_WINDOW'):
                consumer.require_failed_inventory(rows)

    def test_changed_historical_source_raw_or_current_exact_tuple_is_refused(self):
        rows=self.rows();rows[0][1]['sourceSubject']['sha256']='0'*64
        with self.assertRaisesRegex(strict.Refusal,'EXACT_HISTORICAL_FAILED_SOURCE'):
            consumer.require_failed_inventory(rows)
        rows=self.rows();rows[0][1]['rawOutcome']['sha256']='0'*64
        with self.assertRaisesRegex(strict.Refusal,'EXACT_HISTORICAL_FAILED_RAW_OUTCOME'):
            consumer.require_failed_inventory(rows)
        rows=self.rows();rows[14][0]['subject']['sha256']='0'*64
        with self.assertRaisesRegex(strict.Refusal,'EXACT_ACTUAL_FIFTEENTH_ATTEMPT_PIN'):
            consumer.require_failed_inventory(rows)
        rows=self.rows();rows[14][1]['authors']=['/root/SYNTHETIC-WRONG-AUTHOR']
        with self.assertRaisesRegex(strict.Refusal,'EXACT_ACTUAL_FIFTEENTH_ATTEMPT_BODY'):
            consumer.require_failed_inventory(rows)


'''
    return text.replace(marker, controls + marker).encode()


def static_import_closure(bodies, runtime):
    """Derive actual local/stdlib and preserved finite dynamic import closure."""
    local = {Path(name).stem: body for name, body in bodies.items() if name.endswith('.py')}
    trees = {name: ast.parse(body) for name, body in local.items()}
    trees['<isolated-program>'] = ast.parse(assignments(local['test_import_closure'])['ISOLATED_PROGRAM'])
    graph = {name: set() for name in trees}
    exports = {}
    imports = []
    dynamic = []
    contracts = []
    for name, tree in trees.items():
        names = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                names.update(t.id for t in node.targets if isinstance(t, ast.Name))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names.update(a.asname or a.name.split('.')[0] for a in node.names)
        exports[name] = names
    for name, tree in trees.items():
        for node in ast.walk(tree):
            requested = []
            if isinstance(node, ast.Import):
                requested = [(alias.name, None) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                need(not node.level and node.module is not None, 'NO_RELATIVE_IMPORT')
                requested = [(node.module, node.names)]
            for module, symbols in requested:
                top = module.split('.')[0]
                if top in local:
                    need(module == top, 'NO_UNDECLARED_LOCAL_SUBMODULE')
                    if symbols is not None:
                        need(all(alias.name != '*' and alias.name in exports[top] for alias in symbols),
                             'ALL_LOCAL_IMPORT_SYMBOLS_DECLARED')
                    graph[name].add(top)
                    classification = 'EXACT_DECLARED_LOCAL_CODE'
                else:
                    need(top in sys.stdlib_module_names, 'NO_AMBIENT_IMPORT:' + module)
                    classification = 'PYTHON_STDLIB'
                imports.append(dict(source=name, line=node.lineno, module=module,
                                    classification=classification))
            if isinstance(node, ast.Call):
                need(not (isinstance(node.func, ast.Name) and node.func.id == '__import__'),
                     'NO_UNDECLARED_DYNAMIC_IMPORT')
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'import_module':
                    need(name == 'whole_window' and ast.unparse(node) == 'importlib.import_module(name)',
                         'ONLY_PRESERVED_FINITE_DYNAMIC_IMPORT')
                    function = next(x for x in tree.body if isinstance(x, ast.FunctionDef)
                                    and x.name == 'components')
                    names = next(ast.literal_eval(x.value) for x in function.body
                        if isinstance(x, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'names' for t in x.targets))
                    need(type(names) is tuple and set(names) <= set(local), 'FINITE_DYNAMIC_LOCAL_MEMBERS')
                    graph[name].update(names)
                    dynamic.append(dict(source=name, function='components', members=list(names)))
                if isinstance(node.func, ast.Name) and node.func.id in ('closed', 'exact') \
                        and len(node.args) > 1 and isinstance(node.args[1], ast.Constant) \
                        and type(node.args[1].value) is str:
                    contracts.append(dict(source=name, line=node.lineno,
                        validator=node.func.id, keys=node.args[1].value.split()))
    def reach(roots):
        seen = set()
        todo = list(roots)
        while todo:
            name = todo.pop()
            if name not in seen:
                seen.add(name)
                todo.extend(graph[name] - seen)
        return seen
    runtime_names = {Path(name).stem for name in runtime}
    need(reach(runtime_names) == runtime_names and reach(['consumer']) == runtime_names,
         'EXACT_COMPLETE_CURRENT_RUNTIME_IMPORT_CLOSURE')
    return dict(schema='e02-consumer-eose-static-import-closure-v1',
        nodes=sorted(graph), graph={name: sorted(edges) for name, edges in graph.items()},
        imports=imports, finiteDynamicEdges=dynamic, runtime=sorted(runtime_names),
        runtimeCount=len(runtime_names), consumerReachable=sorted(reach(['consumer'])),
        executed=False), contracts


def put(path, value, raw=False):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    body = value if raw else encode(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as output:
        need(output.write(body) == len(body), 'EXACT_OWNED_WRITE')
    return descriptor(path, body)


def build(spec_pin, output):
    pin_shape(spec_pin)
    reader = Reader(require_pre_admission=True)
    reader.admit([spec_pin])
    spec = reader.doc(spec_pin)
    closed(spec, SPEC_KEYS, 'CLOSED_COUPLED_ROOT_SPEC')
    need(spec['schema'] == 'e02-root-consumer-coupled-source2-spec-v1' and spec['actor'] == '/root',
         'ACTUAL_ROOT_COUPLED_SPEC_BEFORE_CAPABILITY_BOOTSTRAP')
    need(spec['rootScope']['sha256'] == SCOPE_SHA and spec['rootScope']['path'] == str(SCOPE)
         and spec['predecessor']['sha256'] == ENTRY_SHA,
         'EXACT_SCOPE_AND_PREDECESSOR_BEFORE_CAPABILITY_BOOTSTRAP')
    for field in FINAL.values():
        need(spec[field] is not None, 'MANDATORY_GENUINE_FINAL_SELECTOR:' + field)
    # Only exact already-pinned governance may bootstrap denial verification.
    template_path = str(OWNED.parents[1] / 'e02-helper-component-basis-contract-20261105/source1/component-basis.UNISSUED.json')
    root24_path = str(OWNED.parents[1] / 'e02-helper-current178-actual-review-20261105/r2/acceptance.json')
    closure_path = str(OWNED.parents[1] / 'e02-helper-current178-actual-review-20261105/r2/final-closure-descriptor.json')
    reader.admit([BOOTSTRAP_EXPECTED[path] for path in (template_path, root24_path, closure_path)])
    template_bootstrap = reader.doc(BOOTSTRAP_EXPECTED[template_path])
    original_root = reader.doc(BOOTSTRAP_EXPECTED[root24_path])
    closure_governance = reader.doc(BOOTSTRAP_EXPECTED[closure_path])
    operational = template_bootstrap['originalBasis']['root24ExpectedPinOperands']
    hashes = {operational[key]['sha256'] for key in ('subject', 'concretePlan', 'rootRelease',
              'execution', 'rawArtifactManifest', 'originalToolOrigin')}
    hashes.add(closure_governance['finalF']['sha256'])
    need(hashes == set(reader.denied_hashes) and original_root['subject'] == operational['subject'],
         'EXACT_PRE_READ_OPERATIONAL_DENIAL_BOOTSTRAP')
    # ALL capabilities are admitted before Source/caller/history/actor fields.
    reader.admit(spec['inputFiles'])
    recipe_pin = spec['preparationRecipe']
    need(recipe_pin['path'] == str(Path(__file__).resolve()), 'EXACT_RUNNING_PREPARATION_RECIPE')
    _, recipe_body = reader.read(recipe_pin['path'], recipe_pin)
    _, consumer_body = reader.read(PREDECESSOR / 'source/consumer.py')
    values = assignments(consumer_body)
    members, basis, template, ordinary = validate_spec(reader, spec, values)
    closure = fixed_closure(reader, spec, values, basis, template)
    closure.add(spec_pin, 'actualRootSpec', 'ROOT_SOURCE_PREPARATION_INPUT')
    closure.add(recipe_pin, 'actualPreparationRecipe', 'SOURCE')
    output = Path(output)
    need(output.is_absolute() and os.path.normpath(str(output)) == str(output)
         and output.parent.resolve(strict=True) == OWNED
         and not output.exists() and not output.is_symlink(), 'FRESH_DIRECT_OWNED_FREEZE_DIRECTORY')
    source = output / 'source'
    code = sorted((*values['RUNTIME_FILES'], *values['CONTROL_FILES'], *EXTRAS))
    need(len(code) == len(set(code)), 'UNIQUE_CODE_MEMBERSHIP')
    bodies = {name: reader.read(PREDECESSOR / 'source' / name)[1] for name in code}
    # All original method definitions and helper parser/import semantics survive
    # the actual coupled freeze; only literal current-selector assignments move.
    original_names = []
    for name in values['CONTROL_FILES']:
        original_names.extend(name + ':' + method for method in methods(bodies[name]))
    need(len(original_names) == len(set(original_names)), 'UNIQUE_SOURCE1_METHOD_PARTITION')
    reader.recheck()
    output.mkdir(mode=0o700)
    def emit(path, value, raw=False):
        pin = put(path, value, raw)
        reader.admit([pin])
        return pin
    for path in sorted((PREDECESSOR / 'contracts').glob('*.json')):
        emit(output / 'contracts' / path.name, reader.read(path)[1], True)
    replacements = {name: spec[field] for name, field in FINAL.items()}
    replacements['CURRENT_CONTROL_ACTORS'] = members
    for name in ('CURRENT_DATA_ACCEPTANCE_CONTRACT', 'CURRENT_CONSUMER_ACCEPTANCE_CONTRACT',
                 'CURRENT_COLLECTOR_PREREQUISITE_CONTRACT'):
        replacements[name] = descriptor(output / 'contracts' / Path(values[name]['path']).name,
            reader.read(values[name]['path'], values[name])[1])
    replacements['UNBOUND_SOURCE_REVISION'] = 'EOSE_COMPONENT_BASIS_ACTUAL_COUPLED_SOURCE2'
    bodies['consumer.py'] = rewrite_assignments(bodies['consumer.py'], replacements)
    clock_record = reader.doc(spec['controlClockSelection'])
    bodies['consumer.py'] = install_clock_source(bodies['consumer.py'], spec['controlClockSelection'],
        clock_record, values['CONTROL_FILES'])
    failed_policy = reader.doc(spec['requiredFailedInventorySelection'])
    bodies['consumer.py'] = install_failed_inventory_source(bodies['consumer.py'],
        spec['requiredFailedInventorySelection'], failed_policy)
    bodies['test_request_families.py'] = adapt_request_fixture(bodies['test_request_families.py'])
    bodies['test_source_bindings.py'] = add_clock_controls(bodies['test_source_bindings.py'])
    bodies['test_data_controls.py'] = add_failed_inventory_controls(bodies['test_data_controls.py'])
    bodies['README.md'] = b'''# Coupled EOSE consumer SOURCE2

This SOURCE selects genuine independently accepted current ordinary286 pure
control evidence and a Root-issued mapping of the unchanged original helper266
components. Original helper strict validators and their R10/266 operands remain
unchanged; ordinary286 has separate parsers. The mapping proves SOURCE equality,
modes and import/environment declarations, not a new live helper observation.

All original352 purposes remain. Two request-family fixtures now use the exact
original helper producer for R10 and the actual corrected ordinary revision.
The pending runtime leaf remains unissued. Consumer SOURCE review, a full fresh
canonical model batch, two genuine ordinary windows, five exports, whole-window
consumption and final integration remain required. No production SDK or release.
'''
    import_closure, closed_calls = static_import_closure(bodies, values['RUNTIME_FILES'])
    emit(output / 'import-closure.json', import_closure)
    emit(output / 'contracts/frozen-closed-contracts.COUPLED.json', dict(
        schema='e02-consumer-coupled-derived-closed-parser-contracts-v1',
        author=AUTHOR, lexicalClosedCalls=closed_calls, runtimeBindingKeys=values['BINDING_KEYS'].split(),
        helperParserNamespace='capture_contracts', ordinaryParserNamespace='ordinary_capture_contracts',
        metadataFloatDomainWidened=False, executionAuthorized=False))
    for name, body in bodies.items():
        emit(source / name, body, True)
    code_pins = {name: descriptor(source / name, body) for name, body in bodies.items()}
    groups = []
    for name in values['CONTROL_FILES']:
        definitions = list(methods(bodies[name]))
        groups.append(dict(name=name, source=code_pins[name], count=len(definitions),
            definitionNames=definitions, argv=['/home/peterhorvath/.miniforge3/bin/python3.13',
            '-I', '-B', str(source / name), '-v'], cwd=str(source),
            format='EXACT_VERBOSE_UNITTEST_NAMES',
            definitionScope='SYNTHETIC_OR_READ_ONLY_DATA_ONLY_NO_TARGET_RUNTIME'))
    total = sum(group['count'] for group in groups)
    plan_pin = emit(source / 'control-plan.json', dict(schema='e02-consumer6-model-control-plan-v1',
        author=AUTHOR, state='COUPLED_SOURCE_DEFINITIONS_NOT_EXECUTED', modelsDefined=total,
        modelsExecuted=0, groups=groups, executionAuthorized=False))
    controller_fixture = dict(schema='e02-consumer-source-read-only-controller-fixture-v1',
        author=AUTHOR, **basis['originalBasis']['controller'],
        meaning='Retained accepted original R10 mock-control operands only; no helper execution or binding authority',
        executionAuthorized=False)
    controller_fixture_pin = emit(output / 'current-inputs.json', controller_fixture)
    closure.add(controller_fixture_pin, 'test_request_families/current-inputs.json', 'SOURCE_FIXTURE')
    for name in ('fixture-authority.json', 'negative-inputs.json'):
        copied_pin = emit(output / name, reader.read(PREDECESSOR / name)[1], True)
        closure.add(copied_pin, 'source2/' + name, 'SOURCE_FIXTURE')
    input_rows = [closure.rows[path] for path in sorted(closure.rows)]
    manifest_pin = emit(source / 'input-manifest.json', dict(schema='e02-consumer6-current-input-manifest-v1',
        author=AUTHOR, fixedSourceAndCurrentDataOperands=input_rows,
        finalInputClosureReady=True, operationalHelperBodiesRead=0,
        opaqueHistoricalNegativeOperands=[closure.opaque[path] for path in sorted(closure.opaque)],
        opaqueHistoricalNegativeMeaning='Exact expected pins preserved without Source body reads; later canonical Root admission and full before/after checks remain mandatory',
        fixedOperandMeaning='Explicit typed Source/governance/pure-control closure; original helper operational operands remain opaque',
        executionAuthorized=False))
    predecessor_subject = reader.doc(reader.doc(spec['predecessor'])['subject'])
    subject = copy.deepcopy(predecessor_subject)
    subject.update(author=AUTHOR, predecessorAuthor='/root/consumer_eose_basis_source',
        sourceContributors=members, sourceRevision=replacements['UNBOUND_SOURCE_REVISION'],
        state='COUPLED_SOURCE_WRITES_STOPPED_PENDING_INDEPENDENT_REVIEW',
        scope='CURRENT_EOSE286_ORIGINAL_HELPER266_COMPONENT_BASIS_CONSUMER_SOURCE_ONLY',
        sourceRoot=str(source), sources=[code_pins[name] for name in code], sourceCount=len(code),
        runtimeSources=[code_pins[name] for name in values['RUNTIME_FILES']],
        runtimeSourceCount=len(values['RUNTIME_FILES']), controlPlan=plan_pin, inputManifest=manifest_pin,
        producerControlAcceptance=spec['producerControlAcceptance'],
        helperComponentBasis=spec['helperComponentBasis'], modelsDefined={g['name']:g['count'] for g in groups},
        modelDefinitions=total, modelGroups=len(groups), modelsExecuted=0,
        completedBasisIssued=True, finalSourceFreezeReady=True,
        runtimeReady=False, executionAuthorized=False)
    subject_pin = emit(source / 'subject.json', subject)
    for name in ('runtime-gates.json',):
        gates = json.loads(reader.read(PREDECESSOR / 'source' / name)[1])
        gates.update(producerSource=values['CURRENT_PRODUCER'],
            producerSourceAcceptance=values['CURRENT_PRODUCER_SOURCE_ACCEPTANCE'],
            producerControlData=spec['producerControlData'],
            producerControlAcceptance=spec['producerControlAcceptance'])
        need(gates['readiness'] is False and gates['issued'] is False
             and gates['helperProbeData'] is None and gates['helperProbeAcceptance'] is None,
             'RUNTIME_BINDING_REMAINS_UNISSUED')
        emit(source / name, gates)
    readmap_pin = emit(output / 'input-read-map.json', dict(schema='e02-consumer-coupled-source2-typed-read-map-v1',
        author=AUTHOR, rows=[dict(pin=closure.rows[path], uses=closure.uses[path]) for path in sorted(closure.rows)],
        recursiveDescriptorWalk=False, operationalHelperBodiesRead=0,
        root24Children='OPAQUE_S18_PLAN_RELEASE_RESULT_MANIFEST_HOST_F_DESCRIPTORS_NOT_FOLLOWED',
        basisFactsMeaning='SOURCE equality/modes/import/environment declarations, not new live helper verification',
        historicalNegativeOpaqueCount=len(closure.opaque),
        noNewPhysicalVerificationClaimForOpaqueOperands=True,
        futureSourceAcceptanceAndConsumerDataAndWindowsExcluded=True, executionAuthorized=False))
    adaptations = []
    for name in values['CONTROL_FILES']:
        before = methods(reader.read(PREDECESSOR / 'source' / name)[1])
        after = methods(bodies[name])
        need(before.keys() <= after.keys(), 'ALL_PREDECESSOR_METHOD_NAMES_PRESERVED')
        adaptations.extend(dict(group=name, method=method,
            oldAstSha256=hashlib.sha256(before[method].encode()).hexdigest(),
            newAstSha256=hashlib.sha256(after[method].encode()).hexdigest(),
            reason='Exact current producer revision or immutable original R10 helper producer fixture')
            for method in before if before[method] != after[method])
    need(len(adaptations) == 2 and all(row['group'] == 'test_request_families.py' for row in adaptations),
         'ONLY_TWO_EXPLICIT_REQUEST_FIXTURE_AST_ADAPTATIONS')
    old_preservation = reader.doc(reader.doc(spec['predecessor'])['preservation'])
    baseline_by_name = {row['name']: row['baseline'] for row in old_preservation['rows']
                        if row.get('baseline') is not None}
    original_count = 0
    original_changes = []
    for name in values['CONTROL_FILES']:
        if name not in baseline_by_name:
            continue
        original = methods(reader.read(baseline_by_name[name]['path'], baseline_by_name[name])[1])
        current = methods(bodies[name])
        need(original.keys() <= current.keys(), 'ALL_ORIGINAL_352_METHOD_NAMES_PRESERVED')
        original_count += len(original)
        original_changes.extend(dict(group=name, method=method,
            originalAstSha256=hashlib.sha256(original[method].encode()).hexdigest(),
            currentAstSha256=hashlib.sha256(current[method].encode()).hexdigest())
            for method in original if original[method] != current[method])
    need(original_count == 352, 'DERIVED_ORIGINAL_352_PARTITION')
    for name in ('capture_contracts.py', 'capture_outputs.py', 'request_families.py'):
        need(bodies[name] == reader.read(baseline_by_name[name]['path'], baseline_by_name[name])[1],
             'ORIGINAL_HELPER_PARSER_AND_IMPORT_SEMANTICS_UNCHANGED')
    original_probe = ast.parse(reader.read(baseline_by_name['probe_adapter.py']['path'],
                                           baseline_by_name['probe_adapter.py'])[1]).body
    current_probe = ast.parse(bodies['probe_adapter.py']).body
    need([ast.dump(node, include_attributes=False) for node in original_probe]
         == [ast.dump(node, include_attributes=False) for node in current_probe[:len(original_probe)]],
         'ORIGINAL_PROBE_FUNCTION_AST_AND_IMPORT_PREFIX_UNCHANGED')
    preservation_pin = emit(output / 'preservation.json', dict(schema='e02-consumer-coupled-source2-preservation-v1',
        predecessor=spec['predecessor'], predecessorMethods=len(original_names),
        allPredecessorMethodNamesPreserved=True, original352PurposesPreserved=True,
        allOtherPredecessorMethodASTPreserved=True, methodAdaptations=adaptations,
        originalMethodsDerived=original_count, originalMethodAstChanges=original_changes,
        productionRequestFunctionChanged='current_control_request: exact Root name-selected finite clock only',
        addedPureMetadataPredicate='control_clock_map',
        originalHelperParsersByteIdentical=True, originalProbeAstAndImportsPreserved=True,
        selectorAssignmentsChanged=sorted(replacements), canonicalModelsExecuted=0,
        failedOrdinaryAttempts=15, failedWindowRowDonation=False))
    # Archive builder, exact spec, readmap and immutable CODE together. There is
    # no later Source acceptance/DATA/window receipt in this backward graph.
    emit(output / 'actual-root-spec.json', reader.read(spec_pin['path'], spec_pin)[1], True)
    emit(output / 'prepare_coupled.py', recipe_body, True)
    files = sorted(path for path in output.rglob('*') if path.is_file())
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for path in files:
            need(not path.is_symlink(), 'NO_ARCHIVE_SOURCE_ALIAS')
            _, body = reader.read(path)
            info = tarfile.TarInfo(str(path.relative_to(output)))
            info.size = len(body)
            info.mode = stat.S_IMODE(path.stat().st_mode)
            info.mtime = info.uid = info.gid = 0
            info.uname = info.gname = ''
            archive.addfile(info, io.BytesIO(body))
    archive_pin = emit(output / 'source.COUPLED.tar', stream.getvalue(), True)
    reader.recheck()
    return emit(output / 'entrypoint.COUPLED.json', dict(schema='e02-consumer-coupled-source2-review-entrypoint-v1',
        author=AUTHOR, state='COUPLED_SOURCE_PENDING_INDEPENDENT_SOURCE_QA_SECURITY',
        subject=subject_pin, archive=archive_pin, rootSpec=spec_pin, readMap=readmap_pin,
        preservation=preservation_pin, modelsDefined=total, modelGroups=len(groups),
        sourceCount=len(code), runtimeSourceCount=len(values['RUNTIME_FILES']),
        canonicalModelsExecuted=0, runtimeBindingIssued=False, executionAuthorized=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', required=True)
    parser.add_argument('--spec-bytes', required=True, type=int)
    parser.add_argument('--spec-sha256', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build(dict(path=args.spec, bytes=args.spec_bytes, sha256=args.spec_sha256), args.output), sort_keys=True))


if __name__ == '__main__':
    main()
