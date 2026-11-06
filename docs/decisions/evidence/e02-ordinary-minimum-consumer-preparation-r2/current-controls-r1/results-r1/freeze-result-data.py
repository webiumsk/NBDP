"""DATA-only freeze of the one finished86 capture, no test/helper/project import."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent
PREP = CAPTURE.parent


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def put_at(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return pin(path)


def main():
    execution_pin = pin(CAPTURE / 'execution.json')
    assert execution_pin['sha256'] == 'f295d4636d0b173c806ed2fac1c6e233b439d3227c64adb5f471d268998a4872'
    execution = json.loads((CAPTURE / 'execution.json').read_bytes())
    before = json.loads((CAPTURE / 'sources-before.json').read_bytes())
    after = json.loads((CAPTURE / 'sources-after.json').read_bytes())
    original_reviews = json.loads((CAPTURE / 'caller-original-reviews-before.json').read_bytes())
    current_reviews = [pin(Path(p['path'])) for p in original_reviews['files']]
    assert current_reviews == original_reviews['files']
    assert pin(Path(original_reviews['rootAcknowledgement']['path'])) == original_reviews['rootAcknowledgement']
    reviews_after = put_at(CAPTURE / 'caller-original-reviews-after.json', dict(
        schema='e02-minimum-consumer-original-source-review-snapshot-v1',
        operation='CALLER_READ_ONLY_EXTRA_ACTUAL_REPORT_CLOSURE', files=current_reviews,
        rootAcknowledgement=original_reviews['rootAcknowledgement'], equalsBefore=True))
    assert before == after and len(before['fullFrozenInputs']) == 176
    for p in before['fullFrozenInputs']: assert pin(Path(p['path'])) == p
    for p in (before['sourceSubject'], before['sourceManifest'], before['frozenSourcePlan'],
              before['monitor'], before['runnerSubject'], before['controlPlan'],
              before['coordinatorAcknowledgement'], *before['sourceReviewRecords']):
        assert pin(Path(p['path'])) == p
    for stream in ('stdout','stderr'):
        path = CAPTURE / ('data.' + stream)
        assert pin(path) == execution[stream] and path.stat().st_mode & 0o777 == 0o600
    for name in ('execution.json','sources-before.json','sources-after.json','started.json',
                 'original-tool-launch-receipt.json','original-tool-poll-01-receipt.json',
                 'caller-original-reviews-before.json','caller-original-reviews-after.json'):
        assert (CAPTURE / name).stat().st_mode & 0o777 == 0o600
    launch = json.loads((CAPTURE / 'original-tool-launch-receipt.json').read_bytes())
    completion = json.loads((CAPTURE / 'original-tool-poll-01-receipt.json').read_bytes())
    association = put_at(CAPTURE / 'tool-association.json', dict(
        schema='e02-minimum-consumer-actual-tool-association-v1', actor='/root/android_health_implementer',
        actualForegroundSession=launch['session_id'], launchToolChunk=launch['chunk_id'],
        completionToolChunk=completion['chunk_id'], actualOuterExitCode=completion['exit_code'],
        originalLaunchResponse=pin(CAPTURE / 'original-tool-launch-receipt.json'),
        originalCompletionResponse=pin(CAPTURE / 'original-tool-poll-01-receipt.json'),
        meaning='Actual available exec_command/write_stdin response fields only, separate from owned child Popen journal; no provider request ID or portable process attestation invented.'))
    raw_files = [pin(p) for p in sorted(CAPTURE.iterdir()) if p.is_file()]
    raw_manifest = put_at(HERE / 'raw-artifact-manifest.json', dict(
        schema='e02-minimum-consumer-control-raw-artifact-manifest-v1', files=raw_files,
        modes={str(p):oct(p.stat().st_mode & 0o777) for p in sorted(CAPTURE.iterdir()) if p.is_file()},
        excludedDirectories=[dict(path=str(CAPTURE/'tmp'), reason='Owned temporary suite DATA namespace; inspect inventory separately'),
                             dict(path=str(HERE), reason='Result freeze files indexed separately to avoid cycles')]))
    temporary = sorted(str(p.relative_to(CAPTURE/'tmp')) for p in (CAPTURE/'tmp').rglob('*'))
    temporary_inventory = put_at(HERE / 'temporary-data-inventory.json', dict(
        schema='e02-minimum-consumer-owned-temp-inventory-v1', paths=temporary,
        meaning='Post-finished read-only inventory only; not a process/descendant cleanup or Android evidence claim.'))
    subject = put_at(HERE / 'subject.json', dict(schema='e02-minimum-consumer-actual-data-controls-subject-v1',
        actor='/root/android_health_implementer', state='WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_RESULT_QA_SECURITY',
        scope='ONE_86_SYNTHETIC_PYTHON_DATA_SUITE_ONLY', sourceSubject=before['sourceSubject'],
        sourceManifest=before['sourceManifest'], runnerSubject=before['runnerSubject'],
        runner=before['monitor'], controlPlan=before['controlPlan'], interpreter=before['interpreter'],
        rootAcknowledgement=before['coordinatorAcknowledgement'], sourceReviewRecords=before['sourceReviewRecords'],
        originalFullSourceReviewsBefore=pin(CAPTURE/'caller-original-reviews-before.json'),
        originalFullSourceReviewsAfter=reviews_after, allEightOriginalSourceReviewRecordsUnchanged=True,
        sourcesBefore=pin(CAPTURE/'sources-before.json'), sourcesAfter=pin(CAPTURE/'sources-after.json'),
        frozenInputCount=176, sourceUnchanged=execution['sourceUnchanged'], execution=execution_pin,
        rawArtifactManifest=raw_manifest, temporaryDataInventory=temporary_inventory, toolAssociation=association,
        actualExpectedCount=execution['expectedCount'], actualObservedCount=execution['observedCount'],
        captureMatched=execution['captureMatched'], actualChildExitCode=execution['exitCode'],
        actualChildSignal=execution['signal'], actualNaturalExit=execution['naturalExit'],
        actualReaped=execution['reaped'], actualStdoutEOF=execution['stdoutEOF'], actualStderrEOF=execution['stderrEOF'],
        actualForceRequested=execution['forceRequested'], actualFirstError=execution['firstError'],
        actualSecondaryErrors=execution['secondaryErrors'], actualElapsedNanoseconds=execution['elapsedNanoseconds'],
        countNotRuntimeInteroperability=True, fullPositiveWholeConsumeGraph=False,
        controlResultAcceptedByAuthor=False, independentReview='PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY',
        noRetry=True, noSourceFixAfterAttempt=True, noAndroidSdkNodeNativeCryptoNetworkServicesExecuted=True,
        cryptographyLimit='Only synthetic/evidence SHA256/NIP01 hashing DATA controls; no protocol sign/encrypt/decrypt/native process ran.',
        retentionMeaning='stdout1MiB/stderr256KiB post-capture retention, not streaming memory caps.',
        sourceV1AndHoldsUnchanged=True, producerSourcesUnchanged=True, canonicalE02='PARTIAL22_UNCHANGED',
        blockers=['Q01','Q08','Q13','Q15','Q27'], freezeScript=pin(Path(__file__).resolve())))
    manifest = put_at(HERE/'artifact-manifest.json', dict(schema='e02-minimum-consumer-actual-result-artifacts-v1',
        files=[pin(p) for p in sorted(HERE.iterdir()) if p.is_file()],
        independentAcceptance='NOT_AUTHORED_BY_OPERATOR'))
    print(json.dumps(dict(state='WRITES_STOPPED',subject=subject,artifactManifest=manifest,
        rawManifest=raw_manifest,actualCount=execution['observedCount'],captureMatched=execution['captureMatched'],
        independentReview='PENDING_ACTUAL_OTHER_AGENTS',tempPaths=len(temporary)),indent=2))


if __name__ == '__main__':
    main()
