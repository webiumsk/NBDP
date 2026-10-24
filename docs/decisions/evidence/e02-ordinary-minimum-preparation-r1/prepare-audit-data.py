"""Read/hash/copy exact source evidence; no NBDP module/test/runtime import."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
E = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1'
SOURCE = Path('/tmp/nbdp-e02-android-artifact/source')
AUDIT = E / 'navigation-source-audit'
COMMIT = 'e6f464a1179def75274512b3c5bab921de3bf3d8'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(path, raw):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)


def main():
    names = ['DrawerSections.kt', 'DrawerContent.kt', 'MessagesSinglePane.kt', 'ChatroomListTabs.kt',
        'AllRelayListScreen.kt', 'LocalRelayListView.kt', 'RelayUrlEditField.kt', 'ActionTopBar.kt',
        'BasicRelaySetupInfoDialog.kt', 'BasicRelaySetupInfoClickableRow.kt', 'RelayNameAndRemoveButton.kt',
        'ChatroomScreen.kt', 'RenderRoomTopBar.kt', 'PrivateMessageEditFieldRow.kt', 'ChatMessageCompose.kt',
        'ChatMessageActionSheet.kt', 'NoteActionSections.kt', 'AppBottomBar.kt', 'NavBarItem.kt',
        'ProfileTopBar.kt', 'UserProfileDropDownMenu.kt', 'TopBarExtensibleWithBackButton.kt', 'Icons.kt',
        'KeyTextField.kt', 'DmInboxRelayState.kt', 'LocalRelayListState.kt', 'NormalizedRelayUrl.kt',
        'BaseDMGroupEvent.kt', 'ChatroomList.kt', 'ChatroomListKnownFeedFilter.kt',
        'ChatroomListNewFeedFilter.kt', 'Account.kt']
    inventory = subprocess.run(['rg', '--files', str(SOURCE)], capture_output=True, timeout=15, check=True)
    files = [Path(line) for line in inventory.stdout.decode().splitlines() if '/src/commonMain/' in line]
    preferred = {'NavBarItem.kt': '/ui/navigation/bottombars/', 'Icons.kt': '/ui/note/',
                 'Account.kt': '/commons/src/commonMain/', 'ChatroomList.kt': '/model/privateChats/'}
    paths = []
    for name in names:
        candidates = [path for path in files if path.name == name]
        if name in preferred:
            candidates = [path for path in candidates if preferred[name] in str(path)]
        if len(candidates) != 1:
            raise ValueError((name, [str(path) for path in candidates]))
        paths.append(candidates[0])
    paths.append(SOURCE / 'commonsUI/src/commonMain/composeResources/values/strings.xml')
    argv = ['git', '--no-optional-locks', '-C', str(SOURCE), 'diff', '--exit-code', COMMIT,
            '--', *[str(path.relative_to(SOURCE)) for path in paths]]
    result = subprocess.run(argv, capture_output=True, timeout=15)
    write(AUDIT / 'git-diff.stdout', result.stdout)
    write(AUDIT / 'git-diff.stderr', result.stderr)
    if result.returncode:
        raise ValueError('Audited source differs from pinned commit; no source authority inferred')
    rows = []
    for path in paths:
        target = AUDIT / 'source' / path.relative_to(SOURCE)
        write(target, path.read_bytes())
        rows.append({'original': pin(path), 'preservedExactBytes': pin(target)})
    for name in ('AndroidManifest.xml', 'src/org/nbdp/clipboard/capture/CaptureActivity.java'):
        path = ROOT / 'experiments/prototypes/e02_ordinary_client_api35_v3/clipboard-helper' / name
        target = AUDIT / 'readonly-helper' / name
        write(target, path.read_bytes())
        rows.append({'original': pin(path), 'preservedExactBytes': pin(target)})
    mapping = [
        ('Your Profile Picture / Profile / More Options / Share', 'ProfileTopBar.kt:121; UserProfileDropDownMenu.kt:101-105; strings:422,5216,4584,5246',
         'Public share chooser preview only; no target selected. Actual nprofile still independently decoded; no declared-account substitute.'),
        ('Feeds -> System -> Relays', 'DrawerSections.kt:105-144; DrawerContent.kt:796-802,915-941',
         'One exact known expanded Feeds header collapse, same-section Reads/Pictures; no enclosure by2px-clipped ancestor or invented collapsed attribute.'),
        ('Relay Settings / Local Relays', 'AllRelayListScreen.kt:314-315,475-483; LocalRelayListView.kt:85-135; strings:5377,4471',
         'Actual LOCAL field between its heading and footer; no neighbouring section or optional forward-profiles Switch.'),
        ('Add a Relay / Add', 'RelayUrlEditField.kt:184-205,224-259; strings:552,3441',
         'Exact typed URL, unique trailing Add inside that field, cleared editor and new LOCAL row. Enabled Add alone is not success.'),
        ('localhost:17777', 'RelayNameAndRemoveButton.kt:64-79; NormalizedRelayUrl.kt:32-36',
         'Exact Local row displayURL text; no whole-screen URL or optional icon-description substitute.'),
        ('Save', 'ActionTopBar.kt:75-80,110-122; AllRelayListScreen.kt:349-362; strings:5758',
         'Exact capitalized Save commits all viewmodels and pops. Subscription/EOSE/wire still independently mandatory.'),
        ('Local DM inbox semantics', 'DmInboxRelayState.kt:43-58; LocalRelayListState.kt:44-59; BasicRelaySetupInfoDialog.kt:36-60',
         'Local relays participate in DM inbox source; row opens RelayInfo. No invented per-row read/write/DM flags.'),
        ('Messages / Known / New Requests', 'NavBarItem.kt:110-112; AppBottomBar.kt:295; MessagesSinglePane.kt:74-75; ChatroomListTabs.kt:93-100; strings:5490,4450,4889',
         'Fresh source-backed tab labels/current bounds; neither tab alone establishes actual account or conversation identity.'),
        ('Archive attribution', 'Account.kt:3933-3946; ChatroomList.kt:74-83,165-167; BaseDMGroupEvent.kt:54-76',
         'Own-author note creates Known room; original recipients minuslocal A yieldsB. Original innerpB is never rewritten.'),
        ('Back / Message or recipient-inbox warning', 'RenderRoomTopBar.kt:87; TopBarExtensibleWithBackButton.kt; Icons.kt:115-118; PrivateMessageEditFieldRow.kt:203-207,218-234,273-304; strings:3609,436,2615',
         'Known navigation/Back + actual expected note + exact one footer branch. Missing-recipient-inbox warning is read only; no send/settings action.'),
        ('Voice call optional', 'ChatroomScreen.kt:49-67; RenderRoomTopBar.kt:115-127; strings:1719',
         'Conditional platform/callingActive feature, never a DM gate and never clicked.'),
        ('Long press / More Options / Copy raw JSON', 'ChatMessageCompose.kt:324-365; ChatMessageActionSheet.kt:475-500; NoteActionSections.kt:224-231; strings:4584,453',
         'Current selected note bounds; exact sheet actions; only actual note.event.toPrettyJson is copied.'),
        ('Clear clipboard / Capture clipboard / guest Back', 'readonly-helper/CaptureActivity.java:29-48; readonly-helper/AndroidManifest.xml',
         'Pinned foreground helper48-char caseId; no expected JSON extra. Default Android Back must return to actual recognized room or fail; no alternate intent/retry.'),
    ]
    record = {'schema': 'e02-minimum-pinned-navigation-source-audit-v1', 'actor': '/root/ordinary_api35_source',
        'sourceCommit': COMMIT, 'upstreamSourceFiles': len(paths),
        'method': 'Read/hash/copy and read-only Git diff. Explorer findings reconciled with exact primary source; no module, test, SDK or runtime execution.',
        'gitDiff': {'argv': argv, 'exitCode': result.returncode, 'stdout': pin(AUDIT / 'git-diff.stdout'),
                    'stderr': pin(AUDIT / 'git-diff.stderr')}, 'sourceInputs': rows,
        'labelToSource': [{'label': label, 'source': source, 'meaning': meaning} for label, source, meaning in mapping],
        'criticalDomAssumptions': [
            'Fresh enabled package/unique label/descendant ownership/current bounds must match source-backed selectors; NOT_RUNTIME_VALIDATED.',
            'Actual new Local text row and cleared field must be visible after Add; absent/ambiguous exposure refuses without another editor/row fallback.',
            'Actual Add a Relay descendant label/trailing Add ancestry are planned source-based XML assumptions, not screenshot attestations.',
            'No post-collapse frame, Known-tab frame or successful message/action/export frame is qualified here.',
            'Header/fullscreen/message placement and visible text-node count remain actual runtime observations; not persistent object identity or global bubble counts.',
            'No new ANR/dialog/shell capability, fixture clipboard fallback, cgroup/action/capture/lease increase or health gate.'],
        'runtimeState': 'NOT_EXECUTED_NOT_RUNTIME_VALIDATED', 'canonicalPromotion': False}
    write(E / 'navigation-source-audit.json', (json.dumps(record, indent=2) + '\n').encode())
    print(json.dumps({'state': 'SOURCE_AUDIT_DATA_PREPARED', 'sourceFiles': len(paths),
                      'gitDiffExit': result.returncode, 'audit': pin(E / 'navigation-source-audit.json')}))


if __name__ == '__main__':
    main()
