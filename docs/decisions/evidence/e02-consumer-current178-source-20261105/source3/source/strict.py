"""Bounded DATA-only primitives. No imports of producers, crypto or services."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

SAFE = 9007199254740991
I64 = 9223372036854775807
DATA = 16777216
FILE = 67108864


class Refusal(ValueError):
    pass


def need(value, reason):
    if not value:
        raise Refusal(reason)


def closed(value, keys):
    need(type(value) is dict and set(value) == set(keys.split()), 'CLOSED_KEYS:' + keys)
    return value


def integer(value, lo=0, hi=SAFE):
    need(type(value) is int and lo <= value <= hi, 'INTEGER_DOMAIN')
    return value


def text(value, limit=65536):
    need(type(value) is str and len(value.encode('utf-8', 'strict')) <= limit, 'UTF8_TEXT_BOUND')
    return value


def hx(value, length=64):
    need(type(value) is str and re.fullmatch('[0-9a-f]{%d}' % length, value), 'HEX_DOMAIN')
    return value


def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def equal(a, b, reason='VALUE_MISMATCH'):
    need(same(a, b), reason)


def loads(raw):
    """Parse before schema validation; all integers initially bounded signed64.

    validate_numbers subsequently narrows every path to SAFE unless explicitly
    registered for that exact root schema. No nested schema can widen its parent.
    """
    need(type(raw) is bytes and len(raw) <= DATA, 'JSON_BYTES_BOUND')
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def number(token):
        need(token != '-0', 'NEGATIVE_ZERO')
        return integer(int(token), -I64, I64)
    def no_number(_):
        raise Refusal('NO_FLOAT_NONFINITE')
    value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
                       parse_int=number, parse_float=no_number, parse_constant=no_number)
    stack, count = [(value, 0)], 0
    while stack:
        item, depth = stack.pop()
        count += 1
        need(depth <= 48 and count <= 250000, 'JSON_STRUCTURE_BOUND')
        if type(item) is str:
            text(item, DATA)
        elif type(item) is dict:
            stack.extend((v, depth + 1) for v in [*item.keys(), *item.values()])
        elif type(item) is list:
            stack.extend((v, depth + 1) for v in item)
    return value


NS_PATHS = {
    'e02-minimum-selection-v1': {('capturedMonotonicNs',)},
    'e02-clipboard-capture-v1': {('elapsedRealtimeNanos',)},
    'e02-single-cell-lease-v1': {(prefix + clock + 'Ns',)
        for prefix in ('issued', 'deadline') for clock in ('Utc', 'Mono', 'Boot')},
    'e02-ordinary-minimum-role-release-v2': {('issuedAtUtcNs',), ('notAfterUtcNs',)},
    'nbdp-e02-acceptance-method-refinement-decision-v1': {('decidedAtUtcNs',)},
    # Consumer-owned witnesses are explicit typed wrappers, not raw tool rewrites.
    'e02-minimum-outer-witness-v1': {('startedUtcNs',), ('finishedUtcNs',)},
    'e02-minimum-resource-witness-v1': {('measuredAtUtcNs',)},
}


def validate_numbers(value):
    schema = value.get('schema') if type(value) is dict else None
    paths = NS_PATHS.get(schema, set())
    stack = [(value, ())]
    while stack:
        item, path = stack.pop()
        if type(item) is int:
            integer(item, 0 if path in paths else -SAFE, I64 if path in paths else SAFE)
        elif type(item) is dict:
            stack.extend((v, path + (k,)) for k, v in item.items())
        elif type(item) is list:
            stack.extend((v, path + (i,)) for i, v in enumerate(item))
    return value


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def pin_shape(pin):
    closed(pin, 'path bytes sha256')
    integer(pin['bytes'], 0, FILE)
    hx(pin['sha256'])
    p = Path(text(pin['path'], 4096))
    need(p.is_absolute() and str(p) == pin['path'] and '..' not in p.parts, 'CANONICAL_PIN_PATH')
    return p


class Files:
    """Exact external roots, no symlink components or rebinds, bounded rereads.

    /session/fixtures and /input bindings are per-window capabilities supplied
    by the independently reviewed window subject. They never rewrite raw bytes.
    """
    def __init__(self, roots):
        self.roots = tuple(Path(p) for p in roots)
        need(self.roots and all(p.is_absolute() for p in self.roots), 'ABSOLUTE_ROOTS')
        self.pins, self.visits, self.total = {}, 0, 0
        self.guest = {}
        self.raw_pins = {}
        self.session_root = None

    def window(self, root):
        self.guest = {}
        self.session_root = Path(root)

    def binding(self, guest, host, window_root):
        p, h = pin_shape(guest), pin_shape(host)
        need(p.is_relative_to('/session/fixtures') or p.is_relative_to('/input'), 'GUEST_CAPABILITY')
        if p.is_relative_to('/session/fixtures'):
            equal(str(h), str(Path(window_root) / 'session/fixtures' / p.relative_to('/session/fixtures')),
                  'GUEST_WINDOW_ESCAPE')
        prior = self.guest.get(str(p))
        need(prior is None or same(prior, host), 'GUEST_BINDING_CONFLICT')
        equal((guest['bytes'], guest['sha256']), (host['bytes'], host['sha256']), 'GUEST_BINDING_BYTES')
        self.guest[str(p)] = host

    def resolved(self, descriptor):
        p = pin_shape(descriptor)
        if p.is_relative_to('/session/fixtures') or p.is_relative_to('/input'):
            if str(p) not in self.guest and p.is_relative_to('/session/fixtures') and self.session_root is not None:
                host = dict(descriptor, path=str(self.session_root / 'session/fixtures' / p.relative_to('/session/fixtures')))
                self.binding(descriptor, host, self.session_root)
            need(str(p) in self.guest, 'UNBOUND_GUEST_PIN')
            actual = self.guest[str(p)]
            equal((actual['bytes'], actual['sha256']), (descriptor['bytes'], descriptor['sha256']))
            return actual
        return descriptor

    def read(self, descriptor, maximum=DATA):
        self.visits += 1
        need(self.visits <= 250000, 'DESCRIPTOR_VISITS_BOUND')
        d = self.resolved(descriptor)
        p = pin_shape(d)
        need(d['bytes'] <= maximum and any(p.is_relative_to(root) for root in self.roots), 'PIN_ADMISSION')
        prior = self.pins.get(str(p),self.raw_pins.get(str(p)))
        need(prior is None or same(prior, d), 'PIN_DRIFT')
        need(prior is not None or (len(set(self.pins)|set(self.raw_pins)) < 20000 and self.total + d['bytes'] <= 536870912), 'GRAPH_BOUND')
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            for component in p.parts[1:-1]:
                newfd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = newfd
            filefd = os.open(p.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        finally:
            os.close(fd)
        with os.fdopen(filefd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            need(stat.S_ISREG(before.st_mode) and before.st_size == d['bytes'], 'REGULAR_SIZE')
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        need(identity(before) == identity(after) and len(raw) == d['bytes']
             and hashlib.sha256(raw).hexdigest() == d['sha256'], 'HASH_IDENTITY_DRIFT')
        if prior is None:
            self.total += len(raw)
        self.pins[str(p)] = dict(d)
        return raw

    def verify_raw(self, descriptor):
        """Stream one explicitly named HOST RAW pin, <=2GiB; never parse it.

        Parsed JSON admission remains16MiB and all existing read() ceilings stay
        unchanged. This method is for the typed helper-probe proof member list.
        """
        self.visits+=1;need(self.visits<=250000,'DESCRIPTOR_VISITS_BOUND')
        closed(descriptor,'path bytes sha256');integer(descriptor['bytes'],0,2147483648);hx(descriptor['sha256'])
        p=Path(text(descriptor['path'],4096))
        need(p.is_absolute() and str(p)==descriptor['path'] and '..' not in p.parts
             and any(p.is_relative_to(root) for root in self.roots),'EXPLICIT_HOST_RAW_PIN')
        prior=self.pins.get(str(p),self.raw_pins.get(str(p)))
        need(prior is None or same(prior,descriptor),'PIN_DRIFT')
        need(prior is not None or (len(set(self.pins)|set(self.raw_pins))<20000 and self.total+descriptor['bytes']<=536870912),'GRAPH_BOUND')
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
        try:
            for component in p.parts[1:-1]:
                newfd=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=newfd
            filefd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        finally:os.close(fd)
        digest=hashlib.sha256();size=0
        identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        with os.fdopen(filefd,'rb') as stream:
            before=os.fstat(stream.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size==descriptor['bytes'],'REGULAR_RAW_SIZE')
            while True:
                chunk=stream.read(1048576)
                if not chunk:break
                size+=len(chunk);need(size<=descriptor['bytes'],'RAW_READ_BOUND');digest.update(chunk)
            after=os.fstat(stream.fileno())
        need(identity(before)==identity(after)==identity(p.lstat()) and size==descriptor['bytes'] and digest.hexdigest()==descriptor['sha256'],'RAW_EXPECTED_PIN_IDENTITY_DRIFT')
        if prior is None:self.total+=size
        self.raw_pins[str(p)]=dict(descriptor)
        return size


    def doc(self, descriptor):
        return validate_numbers(loads(self.read(descriptor)))

    def jsonl(self, descriptor, count=262144):
        raw = self.read(descriptor)
        lines = raw.splitlines()
        need(len(lines) <= count and all(lines), 'JSONL_BOUND_EMPTY')
        return [validate_numbers(loads(line)) for line in lines]

    def recheck(self):
        for d in list(self.raw_pins.values()):self.verify_raw(d)
        for d in list(self.pins.values()):
            self.read(d, FILE)
