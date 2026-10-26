// Solely Bech32 format materialization of the explicitly public disposable scalar1.
import fs from 'node:fs';
import {nsecEncode} from '/home/peterhorvath/apps/bitcoin/NBDP/experiments/node_modules/nostr-tools/lib/esm/nip19.js';
const p='/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/scalar1-format-data/input.json';
const input=JSON.parse(fs.readFileSync(p,'utf8'));
if(Object.keys(input).length!==1||input.scalarHex!=='0'.repeat(63)+'1')throw Error('ONLY_PUBLIC_SCALAR1_DATA');
const nsec=nsecEncode(Uint8Array.from(Buffer.from(input.scalarHex,'hex')));
process.stdout.write(JSON.stringify({schema:'e02-public-scalar1-format-data-v1',scalarHex:input.scalarHex,nsec,operation:'NIP19_FORMAT_ENCODING_ONLY_NO_SIGN_ENCRYPT_NETWORK'})+'\n');
