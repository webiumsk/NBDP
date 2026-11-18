"""Pure helper-R8 metadata rendering SOURCE; no IO, tools, clocks or authority.

Root supplies genuine reservation/lease/verdict/registration values after the
accepted RESERVE step. Outputs are in-memory values; this module creates no
runID, account, lease, grant, file, API origin or runtime execution.
"""

import copy
import hashlib
import json
import re
import shlex


DATA_PARENT = "/Data/nbdp-e02-tooling-20261027/probe-root-custody-actual"
RUNTIME_PARENT = "/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-actual-r1"
GENERIC_KINDS = ("producerData", "sourceQa", "sourceSecurity", "controlData", "concreteInput")
PLAN_WITHOUT_KEYS = set("schema scope runId creationNonce name uidGid inputRoot controlRoot outputRoot dockerConfig lease source8 guardManifest guardRoot tools expectedImageConfigSha256".split())
VERDICT_DECISION = "ACCEPT_CURRENT_CONCRETE_INPUTS_FOR_ONE_HELPER_PROBE_ONLY"


def need(value, reason):
    if not value:
        raise ValueError(reason)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def pin_bytes(path, raw):
    need(type(path) is str and path.startswith("/") and "\x00" not in path and type(raw) is bytes,
         "EXPLICIT_ABSOLUTE_PIN_BYTES")
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def descriptor(value):
    need(type(value) is dict and set(value) == {"path", "bytes", "sha256"}, "CLOSED_PIN")
    need(type(value["path"]) is str and value["path"].startswith("/") and "\x00" not in value["path"]
         and type(value["bytes"]) is int and value["bytes"] > 0
         and type(value["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", value["sha256"]), "EXACT_PIN")
    return value


def fixed_contract(fixed, for_execution=False):
    need(fixed["schema"] == "e02-helper-current-r8-render-templates-v1", "CURRENT_TEMPLATE")
    for pin in fixed["authorities"].values():
        descriptor(pin)
    need(set(fixed["rawSourceGates"]) == {"producerSource", "controllerSource"}, "TWO_RAW_SOURCE_GATES")
    for pin in fixed["rawSourceGates"].values():
        descriptor(pin)
    need(fixed["dataSubjectBindings"] == fixed["rawSourceGates"], "NO_DATA_TRANSFER_ACROSS_SOURCE_TUPLES")
    need(fixed["compiledControllerBindings"]["acceptedProducerSubject"] == fixed["rawSourceGates"]["producerSource"]
         and fixed["compiledControllerBindings"]["source8"] == fixed["planWithoutGates"]["source8"],
         "EXTERNALLY_ACCEPTED_COMPILED_CONTROLLER_JOINS")
    need(descriptor(fixed["hostSource"]) in fixed["controllerRuntimeSources"]
         and fixed["hostSource"]["path"].endswith("/host.py"), "ACCEPTED_CONTROLLER_HOST_SOURCE")
    need(set(fixed["genericGateTemplates"]) == set(GENERIC_KINDS), "EXACT_FIVE_GENERIC_TEMPLATES")
    for kind, gate in fixed["genericGateTemplates"].items():
        need(set(gate) == {"schema", "kind", "actor", "decision", "subject", "evidence", "scope"}
             and gate["schema"] == "e02-one-cid-helper-probe-gate-v1" and gate["kind"] == kind
             and gate["scope"] == "ONE_OWNED_HELPER_PROBE_ONLY" and gate["decision"] is None,
             "UNCHANGED_GENERIC_GATE_SCHEMA")
        if kind == "concreteInput":
            need(gate["subject"] is None and gate["evidence"] is None, "CONCRETE_NOT_PREISSUED")
        else:
            expected = fixed["rawSourceGates"]["producerSource" if kind == "producerData" else "controllerSource"]
            need(gate["subject"] == expected, "EXACT_GENERIC_SOURCE_SUBJECT")
            authority = {"producerData": "producerDataAcceptance", "controlData": "controllerDataAcceptance",
                         "sourceQa": "sourceQaReview", "sourceSecurity": "sourceSecurityReview"}[kind]
            need(gate["evidence"] == fixed["authorities"][authority], "EXACT_CURRENT_UNDERLYING_AUTHORITY")
    if for_execution:
        need(fixed["executionReadiness"] == "FINAL_AUTHORITY_BUNDLE_ACCEPTED_FOR_ROOT_SEQUENCING",
             "BASELINE_COMPONENT_NOT_FINAL_EXECUTION_BUNDLE")


def roster(fixed, actual_operators, additional_authors=()):
    fixed_contract(fixed)
    authors = list(dict.fromkeys([*fixed["trueAuthors"], *additional_authors]))
    operators = list(dict.fromkeys(actual_operators))
    need("/root" in operators and all(type(x) is str and (x == "/root" or x.startswith("/root/"))
         for x in authors + operators), "DISCLOSED_ACTUAL_ROOT_OPERATORS")
    excluded = sorted(set(fixed["conservativeReviewerExclusions"] + authors + operators))
    return {"authors": authors, "operators": operators, "concreteReviewerExclusions": excluded}


def plan_without_gates(fixed, root_run_id, root_nonce, original_lease, original_lease_raw, reservation_ack):
    """Consume Root-supplied values; never issue, sample or relocate a lease."""
    fixed_contract(fixed, for_execution=True)
    need(type(root_run_id) is str and re.fullmatch("[0-9a-f]{32}", root_run_id)
         and root_run_id not in fixed["permanentlyUnavailableRunIds"], "FRESH_ROOT_SELECTED_RUN_ID")
    need(type(root_nonce) is str and re.fullmatch("[0-9a-f]{32}", root_nonce), "ROOT_SELECTED_NONCE")
    account = DATA_PARENT + "/" + root_run_id
    need(set(reservation_ack) == set("reservation reservedInsideMetadataBytes metadataOwnerBytes payloadAvailableBytes grantIssued".split())
         and reservation_ack["reservation"]["path"] == account + "/reservation.json"
         and reservation_ack["reservedInsideMetadataBytes"] == 65536
         and reservation_ack["metadataOwnerBytes"] == 8388608
         and reservation_ack["payloadAvailableBytes"] == 49152
         and reservation_ack["grantIssued"] is False, "GENUINE_RESERVE_ACK_REQUIRED")
    descriptor(reservation_ack["reservation"])
    lease_path = account + "/lease--original.json"
    need(descriptor(original_lease) == pin_bytes(lease_path, original_lease_raw), "SAME_REGISTERED_ORIGINAL_LEASE")
    need(original_lease["bytes"] <= 8192, "BOUNDED_ORIGINAL_LEASE")
    def pairs(rows):
        out = {}
        for k, v in rows:
            need(k not in out, "DUPLICATE_LEASE_KEY")
            out[k] = v
        return out
    def reject(_):
        raise ValueError("INTEGER_LEASE_JSON")
    lease = json.loads(original_lease_raw, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)
    need(set(lease) == set("schema runId bootId issuedUtcNs issuedMonoNs issuedBootNs deadlineUtcNs deadlineMonoNs deadlineBootNs".split())
         and lease["schema"] == "e02-single-cell-lease-v1" and lease["runId"] == root_run_id, "EXACT_ORIGINAL_LEASE_SCHEMA")
    for clock in ("Utc", "Mono", "Boot"):
        start, end = lease["issued" + clock + "Ns"], lease["deadline" + clock + "Ns"]
        need(type(start) is int and type(end) is int and end - start == 1800 * 1000000000,
             "ORIGINAL_NONRENEWABLE_1800")
    plan = copy.deepcopy(fixed["planWithoutGates"])
    root = RUNTIME_PARENT + "/" + root_run_id
    plan.update(runId=root_run_id, creationNonce=root_nonce,
                name="nbdp-helper-probe-" + root_run_id + "-" + root_nonce, lease=copy.deepcopy(original_lease),
                inputRoot=root + "/input", controlRoot=root + "/control", outputRoot=root + "/output",
                dockerConfig=root + "/docker-config")
    need(set(plan) == PLAN_WITHOUT_KEYS, "EXACT_PLAN_WITHOUT_GATES")
    return plan


def concrete_subject(plan_without):
    need(set(plan_without) == PLAN_WITHOUT_KEYS, "NO_GATE_HASH_CYCLE")
    return {"scope": "CURRENT_CONCRETE_INPUTS", "sha256": hashlib.sha256(encoded(plan_without)).hexdigest()}


def validate_concrete_receipt(value, subject, actor_roster):
    need(set(value) == {"schema", "actor", "decision", "subject", "reviews"}
         and value["schema"] == "e02-root-helper-probe-concrete-inputs-v1" and value["actor"] == "/root"
         and value["decision"] == VERDICT_DECISION and value["subject"] == subject, "ACTUAL_ROOT_CONCRETE_RECEIPT")
    need(type(value["reviews"]) is list and len(value["reviews"]) == 2, "ACTUAL_DISTINCT_REVIEW_PAIR")
    sessions = []
    for role, review in zip(("qa", "security"), value["reviews"]):
        need(set(review) == {"role", "session", "decision", "subject"} and review["role"] == role
             and review["decision"] == VERDICT_DECISION and review["subject"] == subject
             and type(review["session"]) is str and review["session"].startswith("/root/")
             and review["session"] not in actor_roster["concreteReviewerExclusions"], "ACTUAL_INDEPENDENT_FOUR_KEY_VERDICT")
        sessions.append(review["session"])
    need(len(set(sessions)) == 2, "DISTINCT_ACTUAL_REVIEW_SESSIONS")


def generic_gate_values(fixed, plan_without, actor_roster, root_concrete_receipt, registered_concrete_pin):
    """Root authenticates original mailbox values and collector ACK externally."""
    fixed_contract(fixed, for_execution=True)
    subject = concrete_subject(plan_without)
    validate_concrete_receipt(root_concrete_receipt, subject, actor_roster)
    path = DATA_PARENT + "/" + plan_without["runId"] + "/gate--concrete-review.json"
    need(descriptor(registered_concrete_pin) == pin_bytes(path, encoded(root_concrete_receipt)), "EXACT_REGISTERED_CONCRETE_RECEIPT")
    values = copy.deepcopy(fixed["genericGateTemplates"])
    need(set(values) == set(GENERIC_KINDS), "FIVE_GENERIC_GATES")
    for kind, gate in values.items():
        gate["decision"] = "ACCEPT"
        if kind == "concreteInput":
            gate.update(subject=subject, evidence=copy.deepcopy(registered_concrete_pin))
        if kind in ("sourceQa", "sourceSecurity"):
            need(gate["actor"] not in actor_roster["authors"] + actor_roster["operators"], "INDEPENDENT_R8_SOURCE_GATE_ACTOR")
    return values


def bind_registered_gates(fixed, plan_without, gate_values, registered_gate_pins):
    fixed_contract(fixed, for_execution=True)
    need(set(plan_without) == PLAN_WITHOUT_KEYS, "EXACT_PLAN_WITHOUT_GATES")
    need(set(gate_values) == set(registered_gate_pins) == set(GENERIC_KINDS), "EXACT_FIVE_REGISTERED_GATES")
    gates = copy.deepcopy(fixed["rawSourceGates"])
    for kind in GENERIC_KINDS:
        path = DATA_PARENT + "/" + plan_without["runId"] + "/gate--" + kind + ".json"
        need(descriptor(registered_gate_pins[kind]) == pin_bytes(path, encoded(gate_values[kind])), "GENUINE_REGISTERED_GATE_PIN")
        gates[kind] = copy.deepcopy(registered_gate_pins[kind])
    plan = copy.deepcopy(plan_without)
    plan["gates"] = gates
    return plan


def root_release_template(fixed, plan, registered_plan_pin, actor_roster):
    """Leaves executionAuthorized NULL: only Root can make its actual decision."""
    fixed_contract(fixed, for_execution=True)
    need(set(plan) == PLAN_WITHOUT_KEYS | {"gates"} and set(plan["gates"]) == set(GENERIC_KINDS) | {"producerSource", "controllerSource"}
         and all(plan["gates"][k] == v for k, v in fixed["rawSourceGates"].items()), "EXACT_CURRENT_SEVEN_GATE_PLAN")
    path = DATA_PARENT + "/" + plan["runId"] + "/plan--concrete.json"
    need(descriptor(registered_plan_pin) == pin_bytes(path, encoded(plan)), "EXACT_REGISTERED_PLAN")
    value = copy.deepcopy(fixed["rootReleaseTemplate"])
    value.update(runId=plan["runId"], creationNonce=plan["creationNonce"], plan=copy.deepcopy(registered_plan_pin),
                 gates=copy.deepcopy(plan["gates"]), authors=actor_roster["authors"], operators=actor_roster["operators"])
    need(value["executionAuthorized"] is None, "ROOT_DECISION_NOT_AUTOMATIC")
    return value


def host_five_key_request(fixed, plan_pin, actual_root_release, registered_release_pin):
    """Render the literal selected request; never strip sandbox-policy fields."""
    fixed_contract(fixed, for_execution=True)
    need(set(actual_root_release) == set("schema actor executionAuthorized runId creationNonce subject plan gates authors operators outerCustodyReservationBytes".split())
         and actual_root_release["schema"] == "e02-one-cid-helper-probe-root-release-v1"
         and actual_root_release["actor"] == "/root" and actual_root_release["executionAuthorized"] is True
         and actual_root_release["plan"] == descriptor(plan_pin), "EXPLICIT_ACTUAL_ROOT_ONE_USE_RELEASE")
    need(plan_pin["path"] == DATA_PARENT + "/" + actual_root_release["runId"] + "/plan--concrete.json"
         and actual_root_release["subject"] == fixed["rawSourceGates"]["controllerSource"]
         and actual_root_release["gates"]["controllerSource"] == actual_root_release["subject"]
         and actual_root_release["gates"]["producerSource"] == fixed["rawSourceGates"]["producerSource"]
         and actual_root_release["outerCustodyReservationBytes"] == 65536, "CURRENT_ROOT_RELEASE_ONLY")
    path = DATA_PARENT + "/" + actual_root_release["runId"] + "/grant--release.json"
    need(descriptor(registered_release_pin) == pin_bytes(path, encoded(actual_root_release)), "REGISTERED_ACTUAL_ROOT_RELEASE")
    host = fixed["hostSource"]["path"]
    python = fixed["planWithoutGates"]["tools"]["python"]["path"]
    tokens = ["/usr/bin/env", "-i", "PATH=/usr/bin:/bin", "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
              "/usr/bin/timeout", "--signal=KILL", "183s", python, "-I", "-B", host,
              "--plan", plan_pin["path"], "--plan-sha", plan_pin["sha256"],
              "--root-release", registered_release_pin["path"], "--root-release-sha", registered_release_pin["sha256"]]
    return {"cmd": shlex.join(tokens), "workdir": host.rsplit("/", 1)[0], "login": False,
            "yield_time_ms": 1000, "max_output_tokens": 2000}
