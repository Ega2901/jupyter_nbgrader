#!/usr/bin/env python3
import argparse, re, os, json, csv, ast, hashlib
from pathlib import Path
from collections import defaultdict
from itertools import combinations
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
try:
    import Levenshtein
except Exception:
    Levenshtein = None
from difflib import SequenceMatcher
from html import escape

_py_comment = re.compile(r"#.*?$", flags=re.M)
_ws = re.compile(r"\s+", flags=re.M)

def read_notebook_code(nb_path: Path) -> list[str]:
    try:
        data = json.loads(nb_path.read_text(encoding="utf-8"))
        return ["".join(c.get("source", [])) for c in data.get("cells", []) if c.get("cell_type")=="code"]
    except Exception:
        return []

def normalize_code(code: str) -> str:
    code = _py_comment.sub("", code)
    code = _ws.sub(" ", code)
    return code.strip()

def ast_fingerprint(code: str) -> str:
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            for attr in ("id","arg","attr"):
                if hasattr(node, attr):
                    setattr(node, attr, "_")
            if isinstance(node, ast.Constant) and isinstance(node.value, (int,float,complex,str,bytes)):
                node.value = "_"
        s = ast.dump(tree, annotate_fields=False, include_attributes=False)
        return hashlib.md5(s.encode()).hexdigest()
    except Exception:
        return ""

def token_ngrams_jaccard(a: str, b: str, n: int=5) -> float:
    def grams(s):
        toks = re.findall(r"[A-Za-z_]\w+|\S", s)
        return set(tuple(toks[i:i+n]) for i in range(max(0,len(toks)-n+1)))
    A, B = grams(a), grams(b)
    return 0.0 if not A or not B else len(A & B)/len(A | B)

def lev_ratio(a: str, b: str) -> float:
    if Levenshtein:
        return Levenshtein.ratio(a,b)
    return SequenceMatcher(a=a, b=b).ratio()

def load_submissions(root: Path, assignment: str):
    res = defaultdict(list)
    for student_dir in sorted(root.glob("*")):
        if student_dir.is_dir():
            adir = student_dir/assignment
            if adir.is_dir():
                res[student_dir.name].extend(sorted(adir.glob("*.ipynb")))
    return res

def build_corpora(subs):
    ids, texts, astfp = [], [], {}
    for sid, files in subs.items():
        parts, fps = [], []
        for nb in files:
            for c in read_notebook_code(nb):
                n = normalize_code(c)
                if n:
                    parts.append(n)
                    fp = ast_fingerprint(n)
                    if fp: fps.append(fp)
        ids.append(sid)
        texts.append("\n".join(parts))
        astfp[sid] = hashlib.md5(("|".join(fps)).encode()).hexdigest() if fps else ""
    return ids, texts, astfp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assignment", required=True)
    ap.add_argument("--root", default="submitted")
    ap.add_argument("--out", default="reports/plag_assignment")
    ap.add_argument("--tfidf_max_features", type=int, default=50000)
    ap.add_argument("--jaccard_n", type=int, default=5)
    ap.add_argument("--flag_threshold", type=float, default=0.82)
    args = ap.parse_args()

    root = Path(args.root)
    out_base = Path(args.out); out_base.parent.mkdir(parents=True, exist_ok=True)

    subs = load_submissions(root, args.assignment)
    if not subs:
        print("[!] нет посылок"); return

    ids, texts, astfp = build_corpora(subs)

    vec = TfidfVectorizer(max_features=args.tfidf_max_features, token_pattern=r"[A-Za-z_]\w+|\S")
    X = vec.fit_transform(texts)
    cos = cosine_similarity(X)

    rows = []
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            s_i, s_j = ids[i], ids[j]
            t_i, t_j = texts[i], texts[j]
            cos_ij = float(cos[i,j])
            jac = token_ngrams_jaccard(t_i, t_j, n=args.jaccard_n)
            lev = lev_ratio(t_i, t_j)
            ast_eq = 1.0 if astfp[s_i] and astfp[s_i]==astfp[s_j] else 0.0
            score = 0.45*cos_ij + 0.25*jac + 0.25*lev + 0.05*ast_eq
            rows.append({
                "student_a": s_i, "student_b": s_j,
                "cosine_tfidf": round(cos_ij,4),
                "jaccard_ngram": round(jac,4),
                "levenshtein": round(lev,4),
                "ast_equal": int(ast_eq),
                "score": round(score,4),
            })

    rows.sort(key=lambda r: r["score"], reverse=True)

    csv_path = out_base.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)

    top = rows[:50]
    def tr(r):
        flag = " style='background:#ffe6e6'" if r["score"]>=args.flag_threshold else ""
        return (f"<tr{flag}><td>{escape(r['student_a'])}</td><td>{escape(r['student_b'])}</td>"
                f"<td>{r['cosine_tfidf']}</td><td>{r['jaccard_ngram']}</td>"
                f"<td>{r['levenshtein']}</td><td>{r['ast_equal']}</td>"
                f"<td><b>{r['score']}</b></td></tr>")

    html = [
        "<html><head><meta charset='utf-8'><title>Plagiarism report</title>",
        "<style>body{font-family:system-ui,Segoe UI,Roboto,Arial} table{border-collapse:collapse} td,th{border:1px solid #ccc;padding:6px 8px}</style>",
        "</head><body>",
        f"<h2>Plagiarism report — {escape(args.assignment)}</h2>",
        f"<p>Pairs: {len(rows)}, Students: {len(ids)}. Flag threshold: {args.flag_threshold}</p>",
        "<table><thead><tr><th>A</th><th>B</th><th>cosine</th><th>jaccard</th><th>lev</th><th>AST eq</th><th>score</th></tr></thead><tbody>",
        *[tr(r) for r in top],
        "</tbody></table>",
        f"<p>Full CSV: {escape(str(csv_path))}</p>",
        "</body></html>"
    ]
    out_base.with_suffix(".html").write_text("\n".join(html), encoding="utf-8")

    print(f"[ok] CSV:  {csv_path}")
    print(f"[ok] HTML: {out_base.with_suffix('.html')}")
    print("[hint] Сверяй пары > threshold вручную, открывая тетради A/B.")

if __name__ == "__main__":
    main()
