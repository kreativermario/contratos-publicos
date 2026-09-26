// Renders scripts/og/og.html into web/static/og.png at exactly 1200x630.
//
// Two things make this more than a --screenshot call. Chrome's headless
// viewport is shorter than the window size it is given (about 86px on macOS),
// and it paints only the viewport: an absolutely positioned footer at the
// bottom of a 630px card simply came out as background. So the page is rendered
// taller and cropped back to 630 here. The crop is done in-process rather than
// with an image library, because the only operation needed is "drop the rows
// below 630" and that is a filter reset plus a re-deflate.
//
// Usage: node scripts/og/build.mjs [path-to-chrome]
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { deflateSync, inflateSync } from 'node:zlib';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, '../../web/static/og.png');
const W = 1200, H = 630, TALL = 760;

const CHROME = process.argv[2] ?? [
	'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
	'/usr/bin/google-chrome', '/usr/bin/chromium'
].find((p) => { try { readFileSync(p); return true; } catch { return false; } });
if (!CHROME) throw new Error('no chrome found; pass its path as the first argument');

const tmp = join(mkdtempSync(join(tmpdir(), 'og-')), 'shot.png');
execFileSync(CHROME, [
	'--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
	'--force-device-scale-factor=1', '--virtual-time-budget=5000',
	`--window-size=${W},${TALL}`, `--screenshot=${tmp}`, join(HERE, 'og.html')
], { stdio: 'ignore' });

/* ---- PNG: undo the per-row filters, keep the first H rows, re-emit ------- */
const src = readFileSync(tmp);
let pos = 8, idat = [], w = 0, h = 0, colour = 0;
while (pos < src.length) {
	const len = src.readUInt32BE(pos), type = src.toString('ascii', pos + 4, pos + 8);
	const body = src.subarray(pos + 8, pos + 8 + len);
	if (type === 'IHDR') { w = body.readUInt32BE(0); h = body.readUInt32BE(4); colour = body[9]; }
	else if (type === 'IDAT') idat.push(body);
	pos += 12 + len;
}
const ch = { 0: 1, 2: 3, 4: 2, 6: 4 }[colour];
if (!ch) throw new Error(`unsupported colour type ${colour}`);
if (w !== W || h < H) throw new Error(`chrome rendered ${w}x${h}, need ${W}x>=${H}`);

const raw = inflateSync(Buffer.concat(idat));
const stride = w * ch;
const rows = [];
let prev = Buffer.alloc(stride), i = 0;
for (let y = 0; y < h; y++) {
	const f = raw[i]; const line = Buffer.from(raw.subarray(i + 1, i + 1 + stride)); i += 1 + stride;
	for (let x = 0; x < stride; x++) {
		const a = x >= ch ? line[x - ch] : 0, b = prev[x], c = x >= ch ? prev[x - ch] : 0;
		if (f === 1) line[x] = (line[x] + a) & 255;
		else if (f === 2) line[x] = (line[x] + b) & 255;
		else if (f === 3) line[x] = (line[x] + ((a + b) >> 1)) & 255;
		else if (f === 4) {
			const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
			line[x] = (line[x] + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c)) & 255;
		}
	}
	rows.push(line); prev = line;
}

const chunk = (type, data) => {
	const out = Buffer.alloc(8 + data.length + 4);
	out.writeUInt32BE(data.length, 0); out.write(type, 4, 'ascii');
	data.copy(out, 8);
	const crcInput = Buffer.concat([Buffer.from(type, 'ascii'), data]);
	out.writeUInt32BE(crc32(crcInput) >>> 0, 8 + data.length);
	return out;
};
let table = null;
function crc32(buf) {
	if (!table) {
		table = new Int32Array(256);
		for (let n = 0; n < 256; n++) {
			let c = n;
			for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
			table[n] = c;
		}
	}
	let c = -1;
	for (const byte of buf) c = table[(c ^ byte) & 0xff] ^ (c >>> 8);
	return c ^ -1;
}

const ihdr = Buffer.alloc(13);
ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4);
ihdr[8] = 8; ihdr[9] = colour;
const body = Buffer.concat(rows.slice(0, H).map((r) => Buffer.concat([Buffer.from([0]), r])));
writeFileSync(OUT, Buffer.concat([
	Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
	chunk('IHDR', ihdr), chunk('IDAT', deflateSync(body, { level: 9 })), chunk('IEND', Buffer.alloc(0))
]));
console.log(`ok: ${OUT} at ${W}x${H}`);
