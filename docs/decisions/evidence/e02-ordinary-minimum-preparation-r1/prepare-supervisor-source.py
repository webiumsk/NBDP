"""SOURCE-only fixed two-window supervisor binding; no worker import/action."""
from pathlib import Path

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
BASE = ROOT / 'experiments/prototypes/e02_ordinary_client_api35_v3/supervisor.py'
OUT = ROOT / 'experiments/prototypes/e02_ordinary_minimum_v1/supervisor.py'
text = BASE.read_text().replace('nbdp-e02-ordinary-client-api35-v3', 'nbdp-e02-ordinary-minimum-v1')
text = text.replace("SCOPE = 'JS_TO_RUST_PEER_INCOMING_SCALAR2_RS_RELAY_ONE_CELL_PARTIAL_ONLY'",
    "SCOPE = 'E02_ORDINARY_MINIMUM_RS_TWO_ROLE_WINDOW_ONLY'\nPROFILE = 'e02-ordinary-minimum-rs-two-role-v1'")
text = text.replace('e02-api35-v3-first-cell-runtime-plan-v1', 'e02-ordinary-minimum-role-runtime-plan-v1')
text = text.replace('e02-api35-v3-first-cell-release-v1', 'e02-ordinary-minimum-role-release-v1')
text = text.replace('e02-api35-v3-first-cell-supervisor-result-v1', 'e02-ordinary-minimum-role-supervisor-result-v1')
text = text.replace("'android_driver.py', 'ui-plan.json', 'fixture.mjs', 'fixture-plan.json')",
    "'android_driver.py', 'ui-plan.json', 'fixture.mjs', 'fixture-plan.json',\n            'minimum-plan.json', 'business-rumor.json', 'chat-rumor.json')")
text = text.replace('def materialize(destination, run_id, seconds):', 'def materialize(destination, run_id, seconds, ordinary_role):')
text = text.replace("    config.update(runId=run_id, originalLeaseSeconds=seconds,",
    """    minimum = strict((HERE / 'minimum-plan.json').read_bytes())
    need(ordinary_role in ('incoming', 'archive'), 'Closed separately granted role required')
    role = minimum['roles'][ordinary_role]
    config.update(profileId=PROFILE, ordinaryRole=ordinary_role, windowId=role['windowId'],
                  account=role['account'], peer=role['peer'],
                  runId=run_id, originalLeaseSeconds=seconds,""")
point = "         'Fixed first slice only')"
addition = """
    need(config['profileId'] == PROFILE and config['ordinaryRole'] in ('incoming', 'archive'),
         'Fixed adopted minimum profile and role required')
    minimum = strict((HERE / 'minimum-plan.json').read_bytes())
    role = minimum['roles'][config['ordinaryRole']]
    need(minimum['profileId'] == PROFILE and config['windowId'] == role['windowId']
         and config['account'] == role['account'] and config['peer'] == role['peer'],
         'Exact fixed account/window bindings required')"""
assert point in text
text = text.replace(point, point + addition, 1)
point = "    for descriptor in fixture['pins'].values():"
text = text.replace(point, "    for descriptor in [*fixture['pins'].values(), *fixture['oracles'].values()]:", 1)
text = text.replace("and env.get('NBDP_FIXTURE_PLAN_SHA256') == digest(HERE / 'fixture-plan.json'),",
    "and env.get('NBDP_FIXTURE_PLAN_SHA256') == digest(HERE / 'fixture-plan.json')\n             and env.get('NBDP_MINIMUM_RUN_CONFIG_SHA256') == self.plan_pin['sha256'],")
text = text.replace("NBDP_FIXTURE_PLAN_SHA256=digest(HERE / 'fixture-plan.json'))",
    "NBDP_FIXTURE_PLAN_SHA256=digest(HERE / 'fixture-plan.json'),\n                           NBDP_MINIMUM_RUN_CONFIG_SHA256=self.plan_pin['sha256'])")
text = text.replace("NBDP_FIXTURE_PLAN_SHA256=os.environ['NBDP_FIXTURE_PLAN_SHA256'])",
    "NBDP_FIXTURE_PLAN_SHA256=os.environ['NBDP_FIXTURE_PLAN_SHA256'],\n               NBDP_MINIMUM_RUN_CONFIG_SHA256=os.environ['NBDP_MINIMUM_RUN_CONFIG_SHA256'])")
text = text.replace("and release['runId'] == config['runId'], 'Exact root first-cell release required')",
    "and release['runId'] == config['runId'] and release['profileId'] == PROFILE\n         and release['ordinaryRole'] == config['ordinaryRole']\n         and release['windowId'] == config['windowId'], 'Exact root first-cell release required')")
text = text.replace("'runId': config['runId'],", "'runId': config['runId'], 'profileId': PROFILE,\n            'ordinaryRole': config['ordinaryRole'], 'windowId': config['windowId'],")
text = text.replace("parser.add_argument('--materialize', type=Path)",
    "parser.add_argument('--materialize', type=Path)\n    parser.add_argument('--ordinary-role', choices=('incoming', 'archive'))")
text = text.replace('materialize(args.materialize, args.run_id, args.seconds)',
    'materialize(args.materialize, args.run_id, args.seconds, args.ordinary_role)')
OUT.write_text(text)
print('Prepared minimum supervisor SOURCE only; no project imports, leases, workers or services.')
