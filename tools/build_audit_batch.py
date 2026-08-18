#!/usr/bin/env python3
"""Build the EXP-G-001 extractor-audit batch: blinded items, UI, LLM chunks, key.

The registered gate (``experiments/gates/EXP-G-001_extractor_audit.yaml``) asks
for **F1 >= 0.95 against adjudicated gold on 300 dual-annotated items**, with
Krippendorff alpha reported. This tool builds the materials for that.

What is different from the v1 audit batch, and why it matters
-------------------------------------------------------------
v1 showed the annotator exactly the features the extractor had claimed and asked
only for their direction. That measures how often a claim the extractor made is
wrong — it can never measure a claim the extractor **missed**, so recall, and
therefore F1, is not computable from it. The gate needs F1.

So each item here carries a **candidate list** that is deliberately NOT the
extractor's output:

* every vocabulary feature whose canonical name or any registered alias appears
  in the text under lenient matching (this over-generates on purpose),
* every feature the extractor claimed,
* plus ``--decoys`` features that the text does not mention at all,

shuffled under the frozen gate seed. The annotator marks a direction for each
candidate *and can add any feature the text claims that is not listed*. Gold is
then the set of (feature, direction) pairs the annotator says the text asserts,
which supports precision, recall and F1 against the extractor's claim set.

The extractor's output never appears in ``audit_batch.jsonl`` or in the UI — it
lives only in the key file. v1 kept it in the batch and asked the annotator not
to look; blindness is now structural rather than requested.

Outputs (no ``.yaml`` — ``validate-configs`` globs ``*.yaml`` under
``experiments/`` and would try to validate one as an experiment):

    audit_batch.jsonl                     blinded items
    audit_key_DO_NOT_SHOW_ANNOTATOR.json  generator, run, stratum, extractor claims
    annotator.html                        self-contained blind UI (no network)
    feature_vocabulary.json               the 76-feature vocabulary + aliases
    README_PROTOCOL.md                    the protocol, sampling design, scoring
    llm_annotation/chunk_NN.md            self-contained prompts for an LLM annotator
    llm_annotation/chunks_manifest.json

Run::

    python tools/build_audit_batch.py --run <run_dir> --out <dir> [--n 300]
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from faithfulids.orchestration.config_loader import load_config  # noqa: E402
from faithfulids.orchestration.references import resolve_reference  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _audit_prompts import FREE_RECALL  # noqa: E402

#: Items per LLM prompt chunk. Small enough that a chunk plus its instructions
#: stays well inside a single response, which is what stopped v1's chunks from
#: truncating mid-item.
CHUNK_SIZE = 25

#: Sampling design, fixed here so it is visible and reviewable rather than
#: chosen while looking at the items. b4/b5 carry the open directional
#: uncertainty and the hardest prose, so they are censused; b0/b1 are
#: deterministic templates and act as the litmus stratum (an annotator or an LLM
#: that disagrees with the extractor THERE is misreading the task, not finding a
#: defect). Counts are capped by what a run actually contains.
DEFAULT_STRATA = {
    "b0_raw_shap": 15,
    "b1_template": 15,
    "b1l_llm_render": 40,
    "b2_zeroshot": 50,
    "b3_dte_style": 60,
    "b4_vte": 60,
    "b5_narrative_vte": 60,
}


def _norm(text: str) -> str:
    """Lowercase, every run of non-alphanumerics -> one space. Mirrors the
    extractor's own normalisation so 'Fwd Packet Length Max' and
    'fwd_packet_length_max' compare equal."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def load_vocabulary() -> dict[str, list[str]]:
    """Canonical feature name -> registered aliases (may be empty)."""
    kb = yaml.safe_load(
        (REPO / "kb" / "feature_semantics" / "cicids2017.yaml").read_text(encoding="utf-8")
    )
    aliases = yaml.safe_load(
        (REPO / "configs" / "extraction_aliases" / "feature_aliases.yaml").read_text(
            encoding="utf-8"
        )
    )["aliases"]
    return {e["name"]: list(aliases.get(e["name"], [])) for e in kb["entries"]}


def candidates_for(text: str, vocab: dict[str, list[str]], claimed: set[str]) -> list[str]:
    """Features the text plausibly mentions, by lenient matching, plus whatever
    the extractor claimed. Over-generation is intended: a candidate list that
    equalled the extractor's output would hand the annotator the answer."""
    ntext = _norm(text)
    hits = set(claimed)
    for canonical, aliases in vocab.items():
        for surface in (canonical, *aliases):
            if _norm(surface) and _norm(surface) in ntext:
                hits.add(canonical)
                break
    return sorted(hits)


def load_run(run_dir: Path) -> list[dict]:
    """Explanations joined to their claim sets.

    The runner appends to ``explanations`` and ``claims`` inside one loop, so the
    two files are positionally aligned; ``claims.jsonl`` carries no generator id
    of its own. The instance ids are re-checked here so a mis-paired export
    fails loudly instead of scoring the wrong text against the wrong claims.
    """
    art = run_dir / "artifacts"
    expl = [json.loads(x) for x in (art / "explanations.jsonl").read_text(
        encoding="utf-8").splitlines() if x.strip()]
    claims = [json.loads(x) for x in (art / "claims.jsonl").read_text(
        encoding="utf-8").splitlines() if x.strip()]
    if len(expl) != len(claims):
        raise SystemExit(f"{run_dir}: {len(expl)} explanations vs {len(claims)} claim sets")
    out = []
    for e, c in zip(expl, claims):
        if e["instance_id"] != c["instance_id"]:
            raise SystemExit(
                f"{run_dir}: explanations/claims are not aligned at {e['instance_id']}"
            )
        out.append({
            "instance_id": e["instance_id"],
            "generator_id": e["generator_id"],
            "text": e["text"],
            "abstained": bool(e.get("abstained")),
            "extractor_version": c["extractor_version"],
            "claims": [{"feature": cl["feature"], "direction": cl["direction"],
                        "direction_evidence": cl.get("direction_evidence")}
                       for cl in c["claims"]],
        })
    return out


def sample(records: list[dict], strata: dict[str, int], rng: random.Random) -> list[dict]:
    """Draw the registered per-generator quota, deterministically."""
    by_gen: dict[str, list[dict]] = {}
    for r in records:
        by_gen.setdefault(r["generator_id"], []).append(r)
    picked: list[dict] = []
    report: list[str] = []
    for gen, want in strata.items():
        pool = sorted(by_gen.get(gen, []), key=lambda r: r["instance_id"])
        take = min(want, len(pool))
        if take < want:
            report.append(f"  {gen}: asked {want}, only {len(pool)} available -> took {take}")
        picked.extend(rng.sample(pool, take) if take < len(pool) else pool)
    for line in report:
        print(line)
    return picked


def build_items(picked: list[dict], vocab: dict[str, list[str]], decoys: int,
                rng: random.Random, run_id: str) -> tuple[list[dict], dict]:
    all_features = sorted(vocab)
    items, key = [], {}
    order = sorted(picked, key=lambda r: (r["generator_id"], r["instance_id"]))
    rng.shuffle(order)  # group and generator are hidden; adjacency must not leak them
    for i, rec in enumerate(order):
        item_id = f"aud2-{i:03d}"
        claimed = {c["feature"] for c in rec["claims"]}
        cands = candidates_for(rec["text"], vocab, claimed)
        pool = [f for f in all_features if f not in cands]
        cands = cands + rng.sample(pool, min(decoys, len(pool)))
        rng.shuffle(cands)
        items.append({
            "item_id": item_id,
            "explanation_text": rec["text"],
            "candidates": cands,
        })
        key[item_id] = {
            "run_id": run_id,
            "instance_id": rec["instance_id"],
            "generator_id": rec["generator_id"],
            "stratum": rec["generator_id"],
            "abstained": rec["abstained"],
            "extractor_version": rec["extractor_version"],
            "extractor_claims": rec["claims"],
        }
    return items, key


def reextract(items: list[dict], key: dict, vocab: dict[str, list[str]]) -> str:
    """Re-run the CURRENT extractor over the audit texts, in place on ``key``.

    The claims frozen in a run's ``claims.jsonl`` belong to whatever extractor
    version produced that run. The gate scores the instrument as it stands now,
    so the prediction side has to be recomputed whenever the extractor moves —
    and it can be, for free: the rule engine is pure Python with no model, no
    GPU and no tokens. Stored beside the original claims rather than replacing
    them, so the attempt log (amendment 0004(D)) keeps both.
    """
    from faithfulids.extraction import build as build_extractor
    from faithfulids.framework import ExplanationRecord

    cfg = load_config("extraction", "eval_extractor")
    version = cfg["version"]
    ext = build_extractor(cfg, llm_client=None, model_config=None,
                          feature_vocabulary=sorted(vocab))
    for it in items:
        iid = it["item_id"]
        claims = ext.extract(ExplanationRecord(
            iid, key[iid]["generator_id"], it["explanation_text"])).claims
        key[iid][f"extractor_claims_{version.replace('.', '_')}"] = [
            {"feature": c.feature, "direction": c.direction.value,
             "direction_evidence": c.direction_evidence} for c in claims
        ]
    return version


# --------------------------------------------------------------------------- #
# The annotator UI. Self-contained: no network, no CDN — the strict-CSP rule
# that applies to published pages is also just good practice for a file an
# annotator opens from disk on a machine we do not control.
# --------------------------------------------------------------------------- #
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root{
    --bg:#f6f7f9; --panel:#fff; --ink:#1a202c; --muted:#64748b; --line:#e2e8f0;
    --accent:#2563eb; --accent-soft:#dbeafe; --pos:#b45309; --pos-bg:#fef3c7;
    --neg:#0e7490; --neg-bg:#cffafe; --unc:#6d28d9; --unc-bg:#ede9fe;
    --abs:#475569; --abs-bg:#e2e8f0; --done:#15803d; --done-bg:#dcfce7; --hl:#fde68a;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0f172a; --panel:#1e293b; --ink:#e2e8f0; --muted:#94a3b8; --line:#334155;
      --accent:#60a5fa; --accent-soft:#1e3a5f; --pos:#fbbf24; --pos-bg:#4a3510;
      --neg:#22d3ee; --neg-bg:#0e3a45; --unc:#c4b5fd; --unc-bg:#312e5e;
      --abs:#cbd5e1; --abs-bg:#33415c; --done:#4ade80; --done-bg:#14401f; --hl:#7a5c00;
    }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:15px/1.55 system-ui,"Segoe UI",Roboto,sans-serif}
  #app{max-width:1180px;margin:0 auto;padding:18px 22px 70px}
  header{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:8px}
  header h1{font-size:17px;margin:0;font-weight:650}
  .spacer{flex:1}
  button{font:inherit;border:1px solid var(--line);background:var(--panel);color:var(--ink);
         border-radius:8px;padding:6px 12px;cursor:pointer}
  button:hover{border-color:var(--accent)}
  button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
  .bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin:4px 0 14px}
  .bar>div{height:100%;background:var(--accent);width:0%;transition:width .2s}
  .meta{color:var(--muted);font-size:13px}
  .cols{display:grid;grid-template-columns:1.3fr 1fr;gap:16px;align-items:start}
  @media (max-width:920px){.cols{grid-template-columns:1fr}}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .text{white-space:pre-wrap;font-size:15px;line-height:1.65}
  .text mark{background:var(--hl);color:inherit;border-radius:3px;padding:0 2px}
  .claim{border:1px solid var(--line);border-radius:10px;padding:9px 11px;margin-bottom:9px}
  .claim.done{border-color:var(--done);background:var(--done-bg)}
  .fname{font-weight:600;font-size:14px;margin-bottom:7px;word-break:break-word}
  .opts{display:flex;gap:6px;flex-wrap:wrap}
  .opt{border-radius:7px;padding:4px 9px;font-size:13px;border:1px solid var(--line)}
  .opt[data-sel="1"]{font-weight:700}
  .opt.pos[data-sel="1"]{background:var(--pos-bg);border-color:var(--pos);color:var(--pos)}
  .opt.neg[data-sel="1"]{background:var(--neg-bg);border-color:var(--neg);color:var(--neg)}
  .opt.unc[data-sel="1"]{background:var(--unc-bg);border-color:var(--unc);color:var(--unc)}
  .opt.abs[data-sel="1"]{background:var(--abs-bg);border-color:var(--abs);color:var(--abs)}
  .hedge{margin-top:6px;font-size:12px;color:var(--muted)}
  .added{border-style:dashed}
  .addrow{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
  .addrow input{font:inherit;padding:6px 9px;border:1px solid var(--line);border-radius:8px;
                background:var(--bg);color:var(--ink);flex:1;min-width:210px}
  textarea{width:100%;font:inherit;padding:8px;border:1px solid var(--line);border-radius:8px;
           background:var(--bg);color:var(--ink);margin-top:10px}
  .nav{display:flex;gap:8px;align-items:center;margin-top:14px;flex-wrap:wrap}
  .grid{display:flex;flex-wrap:wrap;gap:3px;margin-top:12px}
  .cell{width:19px;height:19px;border-radius:4px;border:1px solid var(--line);
        font-size:9px;display:flex;align-items:center;justify-content:center;cursor:pointer}
  .cell.done{background:var(--done);border-color:var(--done);color:#fff}
  .cell.cur{outline:2px solid var(--accent)}
  kbd{background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:0 5px;font-size:12px}
  details{margin:6px 0 14px}
  summary{cursor:pointer;color:var(--accent);font-size:14px}
  .warn{color:var(--pos);font-size:13px}
</style>
</head>
<body>
<div id="app">
<header>
  <h1>__TITLE__</h1>
  <label class="meta">annotator
    <input id="who" placeholder="your name or initials" style="font:inherit;padding:4px 8px;
      border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);width:170px">
  </label>
  <span class="spacer"></span>
  <button id="export" class="primary">Export my annotations</button>
</header>
<div id="boot" class="warn"></div>
<div class="meta" id="buckets"></div>
<div class="meta">Saved in <b>this browser only</b>, under your annotator name. Export
regularly &mdash; clearing site data or a private window loses unexported work.</div>
<div class="meta" id="prog"></div>
<div class="bar"><div id="pbar"></div></div>

<details>
<summary>What am I judging? (read once)</summary>
<div class="panel" style="margin-top:8px">
<p>You read an explanation written about a network-traffic classification. For every
feature listed, say <b>what the text itself claims</b> about that feature's effect
on the predicted class's score:</p>
<ul>
<li><b>+ raises</b> — the text says this feature pushes the score up / toward the predicted class.</li>
<li><b>&minus; lowers</b> — the text says it pushes the score down / away.</li>
<li><b>unclear</b> — the text mentions the feature but does not commit to a direction.</li>
<li><b>absent</b> — the text does not actually talk about this feature. Some listed
features are there precisely because they are <i>not</i> in the text.</li>
</ul>
<p><b>If the text claims a feature that is not in the list, add it</b> using the box at the
bottom of the panel. Missing claims matter as much as wrong ones.</p>
<p>Judge <b>only what the prose says</b>. Do not judge whether the text is correct about the
traffic — that is a different question and not this task. Tick <i>hedged</i> when the text
states a direction but softens it ("may slightly reduce", "possibly lowers").</p>
<p>Keys: <kbd>1</kbd>&hairsp;/&hairsp;<kbd>2</kbd>&hairsp;/&hairsp;<kbd>3</kbd>&hairsp;/&hairsp;<kbd>4</kbd>
set the focused feature, <kbd>&darr;</kbd>&hairsp;/&hairsp;<kbd>&uarr;</kbd> move between features,
<kbd>&rarr;</kbd>&hairsp;/&hairsp;<kbd>&larr;</kbd> change item. Your work saves in this browser
automatically — but export when you finish.</p>
</div>
</details>

<div class="cols">
  <div class="panel"><div class="text" id="text"></div></div>
  <div>
    <div class="panel">
      <div id="claims"></div>
      <div class="addrow">
        <input id="addf" list="vocab" placeholder="The text claims another feature — type its name">
        <datalist id="vocab"></datalist>
        <button id="addbtn">Add</button>
      </div>
      <div class="warn" id="addwarn"></div>
      <textarea id="note" rows="2" placeholder="Note on this item (optional)"></textarea>
    </div>
    <div class="nav">
      <button id="prev">&larr; Previous</button>
      <button id="next" class="primary">Next &rarr;</button>
      <span class="meta" id="itemmeta"></span>
    </div>
    <div class="grid" id="grid"></div>
  </div>
</div>
</div>

<script type="application/json" id="batch-data">__BATCH__</script>
<script type="application/json" id="vocab-data">__VOCAB__</script>
<script>
const ITEMS = JSON.parse(document.getElementById('batch-data').textContent);
const VOCAB = JSON.parse(document.getElementById('vocab-data').textContent);
const BATCH_ID = "__BATCH_ID__";
// Storage is scoped PER ANNOTATOR. The gate needs two independent passes, and
// two people sharing a browser profile under one key would mean the second
// opens the file already holding the first one's answers — which destroys the
// independence the whole dual-annotation design exists to get.
const bucketKey = name => 'audit-' + BATCH_ID + '::' + (name || 'unnamed');
const ACTIVE = 'audit-' + BATCH_ID + '::__active';
const DIRS = [['+','+ raises','pos'],['-','\\u2212 lowers','neg'],
              ['unclear','unclear','unc'],['absent','absent','abs']];

const blank = () => ({annotator:'', ann:{}, notes:{}, added:{}, hedged:{}, i:0});
const load = name => {
  const raw = localStorage.getItem(bucketKey(name));
  const s = raw ? JSON.parse(raw) : blank();
  if(!s.ann) return blank();
  s.annotator = name || '';
  return s;
};
// The annotator name is an in-page field, never a prompt(): a blocked dialog
// (file:// in some browsers, any automated context) throws at load and leaves
// the annotator looking at a silently blank panel.
let state = load(localStorage.getItem(ACTIVE) || '');
let i = state.i || 0, focus = 0;

const save = () => {
  state.i = i;
  localStorage.setItem(bucketKey(state.annotator), JSON.stringify(state));
  localStorage.setItem(ACTIVE, state.annotator || '');
};
const featuresOf = it => (it.candidates || []).concat(state.added[it.item_id] || []);
const isDone = it => featuresOf(it).every(f => (state.ann[it.item_id]||{})[f]);

function highlight(text, feats){
  const esc = text.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
  const uniq = [...new Set(feats)].filter(Boolean).sort((a,b) => b.length - a.length);
  if(!uniq.length) return esc;
  // ONE alternation pass, longest name first. Marking feature by feature would
  // re-match inside the tags it just inserted, and a lookbehind guard against
  // that is not available in every browser an annotator might open this in.
  const pats = uniq.map(f => f.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&').replace(/[_\\s]+/g,'[_\\\\s]+'));
  return esc.replace(new RegExp('(' + pats.join('|') + ')','gi'), '<mark>$1</mark>');
}

function render(){
  const it = ITEMS[i];
  const feats = featuresOf(it);
  document.getElementById('text').innerHTML = highlight(it.explanation_text, feats);
  document.getElementById('itemmeta').textContent = it.item_id;
  const done = ITEMS.filter(isDone).length;
  document.getElementById('prog').textContent =
    'item ' + (i+1) + ' / ' + ITEMS.length + '  \\u2014  ' + done + ' complete';
  document.getElementById('pbar').style.width = (100*done/ITEMS.length) + '%';

  const box = document.getElementById('claims');
  box.innerHTML = '';
  feats.forEach((f, idx) => {
    const cur = (state.ann[it.item_id]||{})[f];
    const added = (state.added[it.item_id]||[]).includes(f);
    const d = document.createElement('div');
    d.className = 'claim' + (cur ? ' done' : '') + (added ? ' added' : '');
    if(idx === focus) d.style.outline = '2px solid var(--accent)';
    const opts = DIRS.map(([v,label,cls]) =>
      '<button class="opt ' + cls + '" data-f="' + encodeURIComponent(f) + '" data-v="' + v +
      '" data-sel="' + (cur === v ? 1 : 0) + '">' + label + '</button>').join('');
    d.innerHTML = '<div class="fname">' + f + (added ? '  <span class="meta">(you added)</span>' : '') +
      '</div><div class="opts">' + opts + '</div>' +
      '<label class="hedge"><input type="checkbox" data-hedge="' + encodeURIComponent(f) + '"' +
      (((state.hedged[it.item_id]||{})[f]) ? ' checked' : '') + '> hedged / softened</label>';
    box.appendChild(d);
  });
  document.getElementById('note').value = state.notes[it.item_id] || '';
  document.getElementById('addwarn').textContent = '';

  const g = document.getElementById('grid');
  g.innerHTML = '';
  ITEMS.forEach((x, n) => {
    const c = document.createElement('div');
    c.className = 'cell' + (isDone(x) ? ' done' : '') + (n === i ? ' cur' : '');
    c.title = x.item_id;
    c.onclick = () => { i = n; focus = 0; save(); render(); };
    g.appendChild(c);
  });
}

document.getElementById('claims').addEventListener('click', ev => {
  const b = ev.target.closest('button.opt');
  if(!b) return;
  const it = ITEMS[i], f = decodeURIComponent(b.dataset.f);
  state.ann[it.item_id] = state.ann[it.item_id] || {};
  state.ann[it.item_id][f] = b.dataset.v;
  focus = featuresOf(it).indexOf(f);
  save(); render();
});
document.getElementById('claims').addEventListener('change', ev => {
  const c = ev.target.closest('input[data-hedge]');
  if(!c) return;
  const it = ITEMS[i], f = decodeURIComponent(c.dataset.hedge);
  state.hedged[it.item_id] = state.hedged[it.item_id] || {};
  state.hedged[it.item_id][f] = c.checked;
  save();
});
document.getElementById('note').addEventListener('input', ev => {
  state.notes[ITEMS[i].item_id] = ev.target.value; save();
});
function addFeature(){
  const it = ITEMS[i], raw = document.getElementById('addf').value.trim();
  const warn = document.getElementById('addwarn');
  if(!raw) return;
  const hit = VOCAB.find(v => v.toLowerCase() === raw.toLowerCase());
  if(!hit){ warn.textContent = 'Not a known feature name — pick one from the list.'; return; }
  if(featuresOf(it).includes(hit)){ warn.textContent = hit + ' is already listed.'; return; }
  state.added[it.item_id] = (state.added[it.item_id] || []).concat([hit]);
  document.getElementById('addf').value = '';
  save(); render();
}
document.getElementById('addbtn').onclick = addFeature;
document.getElementById('addf').addEventListener('keydown', e => { if(e.key === 'Enter') addFeature(); });

const go = d => { i = Math.min(ITEMS.length-1, Math.max(0, i+d)); focus = 0; save(); render(); };
document.getElementById('prev').onclick = () => go(-1);
document.getElementById('next').onclick = () => go(1);
document.addEventListener('keydown', e => {
  if(['INPUT','TEXTAREA'].includes(e.target.tagName)) return;
  const it = ITEMS[i], feats = featuresOf(it);
  if(e.key === 'ArrowRight') go(1);
  else if(e.key === 'ArrowLeft') go(-1);
  else if(e.key === 'ArrowDown'){ focus = Math.min(feats.length-1, focus+1); render(); }
  else if(e.key === 'ArrowUp'){ focus = Math.max(0, focus-1); render(); }
  else if(['1','2','3','4'].includes(e.key) && feats[focus]){
    state.ann[it.item_id] = state.ann[it.item_id] || {};
    state.ann[it.item_id][feats[focus]] = DIRS[+e.key-1][0];
    if(focus < feats.length-1) focus++;
    save(); render();
  } else return;
  e.preventDefault();
});

const nameBox = document.getElementById('who');
nameBox.value = state.annotator || '';
// Switch on 'change' (blur/Enter), never 'input' — switching per keystroke would
// scatter the work across a bucket for every prefix of the name.
nameBox.addEventListener('change', () => {
  const name = nameBox.value.trim();
  if(name === state.annotator) return;
  const existing = localStorage.getItem(bucketKey(name));
  const judged = Object.keys(state.ann).length;
  if(!existing && !state.annotator && judged){
    // started annotating before typing a name: carry that work over, do not lose it
    localStorage.removeItem(bucketKey(''));
    state.annotator = name;
    save();
  } else {
    state = load(name);
    state.annotator = name;
    i = state.i || 0;
    save();
  }
  focus = 0;
  render();
  showBuckets();
});

function showBuckets(){
  const names = Object.keys(localStorage)
    .filter(k => k.startsWith('audit-' + BATCH_ID + '::') && !k.endsWith('__active'))
    .map(k => k.split('::')[1]);
  const others = names.filter(n => n !== (state.annotator || 'unnamed'));
  document.getElementById('buckets').textContent = others.length
    ? 'Other saved passes in this browser: ' + others.join(', ') +
      ' \\u2014 type a name above to switch. Passes are kept separate.'
    : '';
}

document.getElementById('export').onclick = () => {
  if(!state.annotator){ nameBox.focus(); alert('Put your name in the annotator box first — the export is signed with it.'); return; }
  const rows = [];
  ITEMS.forEach(it => {
    const added = state.added[it.item_id] || [];
    featuresOf(it).forEach(f => {
      const d = (state.ann[it.item_id]||{})[f];
      if(!d) return;
      rows.push({item_id: it.item_id, feature: f, text_asserts_direction: d,
                 hedged: !!((state.hedged[it.item_id]||{})[f]), added: added.includes(f)});
    });
    if(state.notes[it.item_id]) rows.push({item_id: it.item_id, note: state.notes[it.item_id]});
  });
  const done = ITEMS.filter(isDone).length;
  const blob = new Blob([JSON.stringify({
    batch_id: BATCH_ID, annotator: state.annotator,
    exported_utc: new Date().toISOString(),
    items_complete: done, items_total: ITEMS.length, annotations: rows
  }, null, 1)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'annotations_' + state.annotator.replace(/\\W+/g,'_') + '.json';
  a.click();
};

document.getElementById('vocab').innerHTML = VOCAB.map(v => '<option value="' + v + '">').join('');
// Surface a start-up failure ON THE PAGE. A silent exception here would leave an
// annotator working against a blank panel with no idea anything was wrong.
try { render(); showBuckets(); }
catch(err){
  document.getElementById('boot').textContent =
    'This page failed to start: ' + err.name + ' \\u2014 ' + err.message +
    '. Please report this instead of annotating.';
}
</script>
</body>
</html>
"""




def write_llm_chunks(items: list[dict], vocab: dict[str, list[str]], out: Path,
                     batch_id: str) -> list[dict]:
    d = out / "llm_annotation"
    (d / "responses").mkdir(parents=True, exist_ok=True)
    vocab_block = "\n".join(f"- `{name}`" for name in sorted(vocab))
    chunks = [items[k:k + CHUNK_SIZE] for k in range(0, len(items), CHUNK_SIZE)]
    manifest = []
    for n, chunk in enumerate(chunks, start=1):
        body = [FREE_RECALL.format(
            title=f"Extractor audit — annotation chunk {n:02d} of {len(chunks):02d}",
            vocab=vocab_block)]
        for it in chunk:
            body.append(f"### {it['item_id']}\n\n```\n{it['explanation_text']}\n```\n")
        body.append(
            f"---\n\nNow output exactly {len(chunk)} JSONL lines, one per item above, "
            f"from `{chunk[0]['item_id']}` to `{chunk[-1]['item_id']}`, in one fenced block."
        )
        (d / f"chunk_{n:02d}.md").write_text("\n".join(body), encoding="utf-8")
        manifest.append({"chunk": f"chunk_{n:02d}.md", "n_items": len(chunk),
                         "first": chunk[0]["item_id"], "last": chunk[-1]["item_id"]})
    (d / "chunks_manifest.json").write_text(
        json.dumps({"batch_id": batch_id, "chunk_size": CHUNK_SIZE,
                    "n_chunks": len(chunks), "chunks": manifest}, indent=1) + "\n",
        encoding="utf-8")
    (d / "validate_llm_annotations.py").write_text(VALIDATOR, encoding="utf-8")
    return manifest


VALIDATOR = '''#!/usr/bin/env python3
"""Check and merge one LLM annotator's chunk replies.

Usage: python validate_llm_annotations.py responses/<model_name>

Checks every item in the manifest is answered exactly once, that directions come
from the allowed set, and that every feature name is in the vocabulary — a model
that invents feature names has not followed the task and its pass is not usable.
Writes ``merged.jsonl`` beside the chunk files on success.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIRS = {"+", "-", "unclear"}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    resp = (HERE / sys.argv[1]).resolve()
    manifest = json.loads((HERE / "chunks_manifest.json").read_text(encoding="utf-8"))
    vocab = set(json.loads((HERE.parent / "feature_vocabulary.json").read_text(encoding="utf-8")))
    batch = [json.loads(x) for x in
             (HERE.parent / "audit_batch.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    expected = [it["item_id"] for it in batch]

    seen, problems, rows = {}, [], []
    for chunk in manifest["chunks"]:
        path = resp / chunk["chunk"].replace(".md", ".jsonl")
        if not path.is_file():
            problems.append(f"missing reply file: {path.name}")
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"{path.name}:{n} is not JSON ({exc.msg}) — usually a truncated "
                                f"last line; ask the model to continue from that item")
                continue
            iid = rec.get("item_id")
            if iid in seen:
                problems.append(f"{path.name}:{n} duplicate answer for {iid}")
            seen[iid] = True
            for c in rec.get("claims") or []:
                if c.get("dir") not in DIRS:
                    problems.append(f"{iid}/{c.get('feature')}: bad dir {c.get('dir')!r}")
                if c.get("feature") not in vocab:
                    problems.append(f"{iid}: {c.get('feature')!r} is not a vocabulary feature")
                rows.append({"item_id": iid, "feature": c.get("feature"),
                             "dir": c.get("dir"), "hedged": bool(c.get("hedged"))})

    for iid in expected:
        if iid not in seen:
            problems.append(f"no answer for {iid}")

    print(f"items answered: {len(seen)}/{len(expected)}   claims: {len(rows)}")
    if problems:
        print(f"\\n{len(problems)} problem(s):")
        for p in problems[:40]:
            print("  -", p)
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1

    out = resp / "merged.jsonl"
    by_item = {}
    for r in rows:
        by_item.setdefault(r["item_id"], []).append(
            {"feature": r["feature"], "dir": r["dir"], "hedged": r["hedged"]})
    with out.open("w", encoding="utf-8", newline="\\n") as fh:
        for iid in expected:
            fh.write(json.dumps({"item_id": iid, "claims": by_item.get(iid, [])},
                                ensure_ascii=False) + "\\n")
    print(f"OK -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", type=Path, required=True, help="run directory to sample from")
    p.add_argument("--out", type=Path, required=True, help="output directory")
    p.add_argument("--n", type=int, default=300, help="target item count (default 300)")
    p.add_argument("--decoys", type=int, default=2,
                   help="unmentioned features added per item (default 2)")
    p.add_argument("--batch-id", default="extractor_audit_v2")
    args = p.parse_args(argv)

    seed = int(resolve_reference("seeds:gates")["extractor_audit"])
    rng = random.Random(seed)
    vocab = load_vocabulary()
    records = load_run(args.run)
    run_id = args.run.name
    versions = {r["extractor_version"] for r in records}
    if len(versions) != 1:
        raise SystemExit(f"mixed extractor versions in {run_id}: {sorted(versions)}")

    strata = dict(DEFAULT_STRATA)
    total = sum(strata.values())
    if total != args.n:
        print(f"NOTE: registered strata sum to {total}, --n is {args.n}; using the strata.")
    picked = sample(records, strata, rng)
    items, key = build_items(picked, vocab, args.decoys, rng, run_id)
    current = reextract(items, key, vocab)

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    with (out / "audit_batch.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    (out / "audit_key_DO_NOT_SHOW_ANNOTATOR.json").write_text(
        json.dumps(key, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (out / "feature_vocabulary.json").write_text(
        json.dumps(vocab, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    blinded = json.dumps(items, ensure_ascii=False)
    html = (HTML
            .replace("__TITLE__", f"Extractor audit — blind annotation ({len(items)} items)")
            .replace("__BATCH__", blinded)
            .replace("__VOCAB__", json.dumps(sorted(vocab), ensure_ascii=False))
            .replace("__BATCH_ID__", args.batch_id))
    (out / "annotator.html").write_text(html, encoding="utf-8")
    chunks = write_llm_chunks(items, vocab, out, args.batch_id)

    counts: dict[str, int] = {}
    for v in key.values():
        counts[v["stratum"]] = counts.get(v["stratum"], 0) + 1
    n_cand = sum(len(it["candidates"]) for it in items)
    (out / "README_PROTOCOL.md").write_text(
        _protocol(args, run_id, sorted(versions)[0], counts, len(items), n_cand,
                  len(chunks), seed), encoding="utf-8")

    print(f"\nbatch {args.batch_id}: {len(items)} items, {n_cand} candidate judgments "
          f"({n_cand/len(items):.1f} per item)")
    for gen, n in sorted(counts.items()):
        print(f"  {gen:<20} {n:>4}")
    print(f"\nwrote {out}/")
    print("  annotator.html                        <- open this in a browser")
    print(f"  llm_annotation/chunk_01..{len(chunks):02d}.md         <- one fresh chat per chunk")
    print("  audit_key_DO_NOT_SHOW_ANNOTATOR.json  <- do not open before annotating")
    return 0


def _protocol(args, run_id, extractor_version, counts, n_items, n_cand, n_chunks, seed) -> str:
    rows = "\n".join(f"| `{g}` | {n} |" for g, n in sorted(counts.items()))
    return f"""# EXP-G-001 extractor audit — blind protocol ({args.batch_id})

Built {datetime.now(timezone.utc).strftime('%Y-%m-%d')} by `tools/build_audit_batch.py`
from run `{run_id}`, extractor **{extractor_version}**, seed **{seed}**
(`seeds:gates:extractor_audit`). Regenerating with the same run and seed
reproduces this batch byte for byte.

## What this gate measures

`experiments/gates/EXP-G-001_extractor_audit.yaml` asks: does the evaluation
claim extractor reach **F1 >= 0.95 against adjudicated gold** on {n_items}
dual-annotated items? F1 is over **(feature, direction) pairs**:

* **gold** — every directional claim two annotators agree the *text* makes,
  after adjudication of their disagreements;
* **prediction** — the claims the extractor produced for that same text.

This is a question about the **instrument**, not about the model. Whether the
text is *right* about the traffic is a different question and is not asked here.

## Why the candidate list is not the extractor's output

The v1 batch listed exactly the features the extractor had claimed and asked only
for their direction. That can measure a claim the extractor got wrong; it can
never measure one it **missed**, so recall — and therefore F1 — was not
computable. Each item here instead lists

* every vocabulary feature whose canonical name or a registered alias appears in
  the text under lenient matching (this over-generates deliberately),
* every feature the extractor claimed,
* plus {args.decoys} features the text does not mention,

shuffled. {n_cand} candidate judgments in total, {n_cand/n_items:.1f} per item.
**The annotator can add any feature the text claims that is not listed** — that
addition is what makes recall measurable. The extractor's output appears nowhere
in `audit_batch.jsonl`, in `annotator.html`, or in the LLM chunks: it is only in
`audit_key_DO_NOT_SHOW_ANNOTATOR.json`. Blindness is structural, not requested.

## Sampling design (fixed before the items were seen)

| stratum | items |
|---|---|
{rows}

`b4_vte` and `b5_narrative_vte` are censused: they carry the hardest prose and
the one open directional uncertainty. `b0_raw_shap` and `b1_template` are
deterministic templates and act as a **litmus stratum** — an annotator who
disagrees with the extractor *there* has misread the task rather than found a
defect. Check that stratum first before trusting the rest of a pass.

## The annotator's task

Open `annotator.html` in any browser. It needs no network and saves to that
browser as you go; **export when you finish**. For each listed feature, record
what the text claims: `+` raises, `-` lowers, `unclear` (named, no direction),
`absent` (not discussed). Tick *hedged* when a direction is softened. Add any
feature the text claims that is not on the list.

Two annotators work **independently** and must not compare notes before both
exports exist. Disagreements are adjudicated afterwards; the adjudicated set is
the gold. Krippendorff alpha is computed on the two independent passes, before
adjudication — adjudicating first would erase the disagreement the statistic
exists to report.

## The LLM annotator

`llm_annotation/` holds {n_chunks} self-contained prompts. One fresh conversation
per chunk, no shared context. Save each fenced JSONL reply to
`llm_annotation/responses/<model>/chunk_NN.jsonl`, then run
`python llm_annotation/validate_llm_annotations.py responses/<model>` to check
completeness and merge.

**The two annotators are elicited differently, and that is deliberate.** The
human UI presents a candidate list and asks for a judgment on each; the LLM is
asked for free recall against the vocabulary. A candidate list would hand a
language model most of the answer, and free recall would make a human's pass
slow and inconsistent. Both modes produce the same object — a set of
(feature, direction) claims about the text — so both score against gold the same
way. For agreement, the unit set is every (item, feature) pair either annotator
names, with "not claimed" as an explicit category; a feature one annotator lists
and the other omits is a disagreement, not a missing value. Report the
elicitation difference with the alpha: it is a plausible source of systematic
disagreement and a reader should not have to discover it from the code.

**A caution that is on the record.** A second LLM annotator was already tried on
the v1 batch and **excluded**: Krippendorff alpha 0.02 against the human pass,
with 74% spurious `absent` judgments on features that were verbatim in the text.
Check the litmus stratum before accepting any LLM pass as an annotator. An LLM
that disagrees with the deterministic `b0`/`b1` templates is not annotating.

## Gate-failure clause (prereg amendment 0001)

If the gate fails, the legal move is: **the instrument iterates, the annotation
is fixed, and every attempt is logged.** The extractor may be revised and
re-gated (semver bump, changelog, re-run). The gold set is never edited to meet
the threshold. Every attempt is recorded whether it passes or not.
"""


if __name__ == "__main__":
    raise SystemExit(main())
