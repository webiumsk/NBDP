#!/usr/bin/env python3
"""Freeze SOURCE metadata only; do not import or execute NBDP runtime code."""

import copy
import hashlib
import json
import os
from pathlib import Path


ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
OUT = Path(__file__).resolve().parent
BASE = Path('/Data/nbdp-e02-tooling-20261027/helper-probe-concrete-preparation-r1/current-r6')
ACTOR = '/root/helper_r6_binding'
EVIDENCE = ROOT / 'docs/decisions/evidence'
PRODUCER_ACCEPTANCE = EVIDENCE / 'e02-producer4-266-control-actual-20261029/acceptance.json'
EXPECTED_SUBJECT_SHA = '5013b22644e90a82d10792c456440e34faa1b1b2a5a033ac2f29282e4f14ad92'
PAYLOADS = []


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def load(path):
    return json.loads(Path(path).read_bytes())


def put(name, value=None, raw=None):
    path = OUT / name
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    body = encoded(value) if raw is None else raw
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(body)
    PAYLOADS.append(path)
    return pin(path)


def descriptors(value, pointer=''):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            yield pointer, value
        for key, child in value.items():
            yield from descriptors(child, pointer + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from descriptors(child, pointer + '/' + str(i))


def verified(descriptor):
    if pin(descriptor['path']) != descriptor:
        raise ValueError('Introduced descriptor mismatch: ' + descriptor['path'])
    return load(descriptor['path'])


def changes(before, after, pointer=''):
    if type(before) is not type(after):
        return [{'pointer': pointer, 'before': before, 'after': after}]
    if isinstance(before, dict):
        rows = []
        for key in sorted(before.keys() | after.keys()):
            child = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in before:
                rows.append({'pointer': child, 'operation': 'add', 'after': after[key]})
            elif key not in after:
                rows.append({'pointer': child, 'operation': 'remove', 'before': before[key]})
            else:
                rows.extend(changes(before[key], after[key], child))
        return rows
    if before != after:
        return [{'pointer': pointer, 'before': before, 'after': after}]
    return []


def main():
    # All writes stay in the assigned new SOURCE namespace. Existing files cause refusal.
    original = {name: load(BASE / name) for name in ('source8-overlay.json', 'render-delta.json', 'review-entrypoint.json')}
    preserved = []
    for name in original:
        source = pin(BASE / name)
        saved = put('preserved/current-r6/' + name, raw=(BASE / name).read_bytes())
        if (source['bytes'], source['sha256']) != (saved['bytes'], saved['sha256']):
            raise ValueError('Predecessor copy mismatch')
        preserved.append({'original': source, 'copy': saved, 'originalMode': oct((BASE / name).stat().st_mode & 0o777)})

    acceptance = load(PRODUCER_ACCEPTANCE)
    if acceptance['decision'] != 'ACCEPT_PRODUCER4_CURRENT_266_PURE_CONTROL_DATA_ONLY':
        raise ValueError('Wrong producer acceptance scope')
    if [acceptance[k] for k in ('modelsExecuted', 'modelsPassed', 'modelsFailed')] != [266, 266, 0]:
        raise ValueError('Wrong producer model counts')
    if acceptance['countsSeparate'] != [129, 33, 29, 16, 20, 10, 11, 8, 7, 3]:
        raise ValueError('Wrong producer groups')
    if acceptance['subject']['sha256'] != EXPECTED_SUBJECT_SHA:
        raise ValueError('Wrong current producer DATA subject')
    if acceptance['executionAuthorized'] is not False or acceptance['runtimeAuthorized'] is not False:
        raise ValueError('Pure-control DATA does not authorize runtime')
    for _, descriptor in descriptors(acceptance):
        verified(descriptor)
    producer_reviews = [verified(row) for row in acceptance['reviews']]
    if [review['role'] for review in producer_reviews] != ['qa', 'security']:
        raise ValueError('Missing producer review pair')
    if len({review['session'] for review in producer_reviews}) != 2:
        raise ValueError('Producer reviewers not distinct')
    if any(review['subject'] != acceptance['subject'] or review['decision'] != acceptance['decision'] for review in producer_reviews):
        raise ValueError('Producer reviews select different DATA')
    capture_source_acceptance = verified(acceptance['captureSourceAcceptance'])
    admission_acceptance = verified(acceptance['admissionDataAcceptance'])
    verified(admission_acceptance['subject'])
    if capture_source_acceptance['subject'] != acceptance['captureSource']:
        raise ValueError('Capture SOURCE join mismatch')
    if admission_acceptance['captureSource'] != acceptance['captureSource'] or admission_acceptance['producerSource'] != acceptance['producerSource']:
        raise ValueError('Capture admission join mismatch')

    overlay = copy.deepcopy(original['source8-overlay.json'])
    delta = copy.deepcopy(original['render-delta.json'])
    entry = copy.deepcopy(original['review-entrypoint.json'])
    producer_acceptance_pin = pin(PRODUCER_ACCEPTANCE)
    producer = overlay['currentProducer']
    if producer['source'] != acceptance['producerSource'] or producer['sourceAcceptance'] != acceptance['producerSourceAcceptance']:
        raise ValueError('Current producer SOURCE join mismatch')
    producer.update({
        'actualDataAcceptance': producer_acceptance_pin,
        'actualDataSubject': acceptance['subject'],
        'actualDataReviews': acceptance['reviews'],
        'currentCaptureSource': acceptance['captureSource'],
        'currentCaptureSourceAcceptance': acceptance['captureSourceAcceptance'],
        'currentCaptureAdmissionData': admission_acceptance['subject'],
        'currentCaptureAdmissionDataAcceptance': acceptance['admissionDataAcceptance'],
    })
    overlay['issuedCurrentAuthorities']['producerData266Acceptance'] = producer_acceptance_pin
    overlay['unissuedDrafts']['genericGates']['producerData']['evidence'] = producer_acceptance_pin
    overlay['unissuedDrafts']['helperSubject18']['producerDataAcceptance'] = producer_acceptance_pin

    # Preserve the original 13 actual source/design contributors; this preparation adds one author.
    authors = overlay.pop('futureRootReleaseAuthors13') + [ACTOR]
    exclusions = overlay.pop('conservativeReviewerExclusions22') + [ACTOR]
    if len(authors) != len(set(authors)) or len(exclusions) != len(set(exclusions)):
        raise ValueError('Duplicate participant')
    overlay['futureRootReleaseAuthors14'] = authors
    overlay['preparationContributors'] = [ACTOR]
    overlay['conservativeReviewerExclusions23'] = exclusions
    overlay['unissuedDrafts']['helperSubject18']['authors'] = authors
    overlay['unissuedDrafts']['rootRelease']['authors'] = authors
    overlay['independenceRule'] = 'Exclude all 23 declared conservative actors, including this preparation author, plus actual operators and every further disclosed contributor. Future release authors include all original 13 source/design contributors and this preparation author. Read-only verdict authors are not relabelled implementation authors.'
    overlay['author'] = ACTOR
    overlay['state'] = 'FROZEN_METADATA_FOR_INDEPENDENT_SOURCE_REVIEW_NO_RUNTIME_AUTHORITY'
    overlay['precedence'] = 'Replaces only the pending current-r6 producer266 NULL authority joins and records the additional preparation author. Exact accepted subject5013b226 and acceptance/reviews/capture/admission joins select the fresh corrected run. Original current-r6 bytes and prior failed quoted-command run remain preserved. All existing R8 SOURCE/168 DATA and current-r3 custody, clock, isolation, gate and budget contracts are unchanged. No runtime recursive merge or grant.'
    overlay['currentGenericInputs']['meaning'] = 'Historical generic538 observation from 2026-10-29 only; not a current host, daemon, image or continuous immutability claim. Its frozen NULL DATA placeholders remain documentary. This overlay binds independently issued DATA separately. Re-observe and independently review current concrete inputs before any fresh lease/release.'
    overlay['historicalGenericObservationOnly'] = True
    overlay['readiness'] = False
    overlay['executionAuthorized'] = False

    delta['author'] = ACTOR
    delta['awaitingActualProducer266Data'] = False
    delta['state'] = overlay['state']
    delta['admissionBeforeRelease'][0] = 'Verify the exact issued current producer SOURCE13/current266 acceptance189a8564 subject5013b226 and complete review/capture/admission joins selected by this packet; currentR8 SOURCE14/current168 DATA20 remain prerequisites only. No old260 or R7 result transfer.'
    delta['admissionBeforeRelease'][1] = 'Treat the source8 generic538 packet as historical observation only. Restore and verify exact guard manifest/root, then re-observe and independently review all current concrete input closure, tools/daemon/image and expected0444 modes before a fresh release.'
    delta['admissionBeforeRelease'][4] = 'Freshly encode/pin every actual plan/gate/receipt/grant/API/M4/S18 after all current authority substitutions and the full original13 plus preparation author/operator union; charge every physical operational copy in the same account.'
    delta['replacements'][1]['replacement'] = 'Current producer subjectfe619 and actual whole266 DATA subject5013b226, Root acceptance189a8564, exact QA/security reviews and capture/admission joins are bound here. Old260/43ff and the quoted-command predecessor remain historical.'
    delta['replacements'][4]['replacement'] = 'The source8 generic538 packetr4/463c remains historical only. Fresh concrete admission requires current actual input observations and exact guard restoration; documentary NULL authority fields never substitute for issued authority.'
    delta['replacements'][5] = {
        'selector': '/futureRootReleaseAuthors14 and /conservativeReviewerExclusions23',
        'replacement': 'Preserve the original13 actual source/design authors, add /root/helper_r6_binding as preparation author, exclude the full23 conservative actors plus all actual operators/further disclosed contributors. Do not manufacture review independence.',
    }
    entry.update({
        'author': ACTOR,
        'state': overlay['state'],
        'currentProducerData266Acceptance': producer_acceptance_pin,
        'currentProducerData266Subject': acceptance['subject'],
        'knownCreatorCount': len(authors),
        'conservativeReviewerExclusionCount': len(exclusions),
        'copyScope': 'The three original pending preparation documents are preserved byte-identically in this new SOURCE namespace. Completed metadata only; no operational run proof, runtime input binary, helper execution, lease/account/grant or concrete acceptance is created.',
        'remainingGates': [
            'Independent review of this exact completed current-r6 SOURCE metadata and the full creator/operator exclusion union; producer266/controller168 are prerequisite controls only.',
            'Restore and verify the exact unavailable guard manifest/root; then obtain fresh current tool/daemon/image/whole-input observations and independent concrete review. Historical538 observations do not establish current admission.',
            'Root alone selects a fresh runID/nonce, precharges the unchanged single65536 account inside metadata8MiB, issues a fresh original1800 lease and receives both actual volatile concrete verdicts.',
            'Recompute full-chain payload/ledger/remaining-proof fit and issue a separately fresh one-use Root release. Preserve the unchanged current-r3 final-F platform-witness boundary.',
            'After actual helper DATA, obtain independent result acceptance and new current consumer/completion bindings before ordinary role observations.',
        ],
        'historicalGenericObservationOnly': True,
    })

    joins = {
        'schema': 'e02-helper-current-r6-authority-joins-v1',
        'actor': ACTOR,
        'scope': 'SOURCE_METADATA_ONLY_NO_RUNTIME_AUTHORITY',
        'producerAcceptance': producer_acceptance_pin,
        'producerDataSubject': acceptance['subject'],
        'producerDataReviews': acceptance['reviews'],
        'producerSource': acceptance['producerSource'],
        'producerSourceAcceptance': acceptance['producerSourceAcceptance'],
        'captureSource': acceptance['captureSource'],
        'captureSourceAcceptance': acceptance['captureSourceAcceptance'],
        'captureAdmissionData': admission_acceptance['subject'],
        'captureAdmissionDataAcceptance': acceptance['admissionDataAcceptance'],
        'controllerSourceAcceptance': overlay['issuedCurrentAuthorities']['controllerSourceAcceptance'],
        'controllerDataAcceptance': overlay['issuedCurrentAuthorities']['controllerControlDataAcceptance'],
        'producerReviewSessions': [review['session'] for review in producer_reviews],
        'executionAuthorized': False,
        'noOldResultTransfer': True,
    }
    # Verify new issued authority descriptors, independently of inherited historical references.
    for _, descriptor in descriptors(joins):
        verified(descriptor)
    controller_source = verified(joins['controllerSourceAcceptance'])
    controller_data = verified(joins['controllerDataAcceptance'])
    if controller_source['subject'] != overlay['currentSource8']['controllerSource'] or controller_data['controllerSource'] != controller_source['subject']:
        raise ValueError('Current controller SOURCE/DATA mismatch')
    if [controller_data[k] for k in ('modelsExecuted', 'modelsPassed', 'modelsFailed')] != [168, 168, 0]:
        raise ValueError('Wrong controller control counts')

    # Preserve original budget/clock/guest/runtime mechanics exactly.
    if delta['sameBudget'] != original['render-delta.json']['sameBudget']:
        raise ValueError('Budget changed')
    for key in ('unchanged', 'currentSource8', 'actualPending', 'compactConcreteReceiptContract'):
        if overlay[key] != original['source8-overlay.json'][key]:
            raise ValueError('Protected metadata changed: ' + key)
    if any(value is not None for value in overlay['actualPending'].values()):
        raise ValueError('Runtime placeholder was issued')
    if any(overlay['unissuedDrafts'][key]['executionAuthorized'] is not False for key in ('hostOuter', 'rootRelease')):
        raise ValueError('Runtime authorization created')

    rows, observed = [], {}
    for label, document in (('overlay', overlay), ('joins', joins)):
        for pointer, descriptor in descriptors(document):
            path = descriptor['path']
            if path not in observed:
                try:
                    observed[path] = pin(path)
                except OSError as error:
                    observed[path] = {'path': path, 'error': type(error).__name__}
            actual = observed[path]
            rows.append({'location': label + pointer, 'expected': descriptor, 'observed': actual, 'matches': actual == descriptor})
    failures = [row for row in rows if not row['matches']]
    if any(row['expected']['path'] != '/tmp/nbdp-e02-minimal-rs-v7/records/guard-bundle-manifest.json' or row['observed'].get('error') != 'FileNotFoundError' for row in failures):
        raise ValueError('Unexpected inherited descriptor discrepancy; preserve and investigate before freezing')
    verification = {
        'schema': 'e02-helper-current-r6-readonly-descriptor-observation-v1',
        'actor': ACTOR,
        'scope': 'READ_ONLY_FILE_BYTES_AT_PREPARATION_NO_RUNTIME_OR_CONTINUOUS_IMMUTABILITY_CLAIM',
        'descriptorOccurrences': len(rows),
        'distinctPaths': len(observed),
        'mismatchOccurrences': len(failures),
        'missingDistinctPaths': sorted({row['expected']['path'] for row in failures}),
        'introducedAuthorityJoinsVerified': True,
        'runtimeReady': False,
        'rows': rows,
    }
    overlay['preparationInputAvailability'] = {
        'state': 'MISSING_PINNED_RUNTIME_GUARD_MANIFEST_REQUIRES_EXACT_RESTORATION',
        'missingPath': '/tmp/nbdp-e02-minimal-rs-v7/records/guard-bundle-manifest.json',
        'historicalExpectedDescriptorPreserved': True,
        'guardRootRevalidationRequired': True,
        'runtimeAuthorized': False,
    }
    overlay_pin = put('source8-overlay.json', overlay)
    delta_pin = put('render-delta.json', delta)
    joins_pin = put('authority-joins.json', joins)
    verification_pin = put('descriptor-verification.json', verification)
    preservation_pin = put('preservation-and-diff.json', {
        'schema': 'e02-helper-current-r6-preservation-and-diff-v1',
        'actor': ACTOR,
        'predecessors': preserved,
        'changes': {
            'source8-overlay.json': changes(original['source8-overlay.json'], overlay),
            'render-delta.json': changes(original['render-delta.json'], delta),
            'review-entrypointSemanticMetadataBeforeFinalPacketPins': changes(original['review-entrypoint.json'], entry),
        },
        'diffScope': 'Complete overlay/render-delta changes and semantic entrypoint changes before adding this packet\'s generated descriptors. Final packet pins and file count are inspectable directly in the entrypoint/manifest; excluding them here prevents a hash cycle.',
        'protectedSectionsByteSemanticsUnchanged': ['currentSource8', 'unchanged', 'actualPending', 'compactConcreteReceiptContract', 'render-delta.sameBudget'],
        'originalsRecheckedAtEnd': [pin(BASE / name) for name in original],
        'sourcePreparationOnly': True,
        'executionAuthorized': False,
    })
    manifest = {
        'schema': 'e02-helper-current-r6-source-packet-manifest-v1',
        'actor': ACTOR,
        'scope': 'METADATA_SOURCE_PACKET_ONLY',
        'files': [pin(path) for path in [Path(__file__).resolve()] + PAYLOADS],
        'excludesSelfAndEntrypointToRemainAcyclic': True,
        'executionAuthorized': False,
    }
    manifest_pin = put('manifest.json', manifest)
    entry.update({
        'overlay': overlay_pin,
        'renderDelta': delta_pin,
        'authorityJoins': joins_pin,
        'descriptorVerification': verification_pin,
        'preservationAndDiff': preservation_pin,
        'manifest': manifest_pin,
        'filesDefined': len(manifest['files']) + 2,
        'readiness': False,
        'executionAuthorized': False,
        'missingRuntimeInputs': verification['missingDistinctPaths'],
        'freezeMeaning': 'Immutable SOURCE metadata candidate for independent review. It is not Root acceptance, a runtime approval or a claim that runtime prerequisites are currently available.',
    })
    entrypoint = put('review-entrypoint.json', entry)
    print(json.dumps({'entrypoint': entrypoint, 'filesDefined': entry['filesDefined'], 'missingRuntimeInputs': entry['missingRuntimeInputs'], 'runtimeAuthorized': False}, indent=2))


if __name__ == '__main__':
    main()
