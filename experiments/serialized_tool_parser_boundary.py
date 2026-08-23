from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

POLICIES = ("lenient_raw", "strict_schema", "strict_fresh", "canonical_fresh")
ATTACKS = (
    "duplicate_field",
    "unknown_field",
    "numeric_coercion",
    "nonfinite_nan",
    "nonfinite_inf",
    "overflow_negative",
    "underflow_tiny",
    "negative_zero",
    "boolean_integer",
    "missing_field",
    "unit_confusion",
    "unicode_tool",
    "unicode_confusable",
    "oversized_payload",
    "schema_mismatch",
    "security_field_injection",
    "token_replay",
    "precision_smuggle",
)
TOOLS = ("read", "write", "delete", "transfer")

PROTECTED_RESOURCES = {"r0", "r3", "r7"}
WRITE_MAX = 0.12
TRANSFER_MAX = 0.10
SCHEMA_VERSION = 2
MAX_PAYLOAD_BYTES = 16_384
MAX_DECIMAL_PLACES = 6


@dataclass(frozen=True)
class Token:
    token_id: str
    version: int
    nonce: int
    tool: str
    subject: str
    max_amount: float


@dataclass
class Decoded:
    tool: str
    args: Dict[str, Any]
    token: Token | None
    canonical: str | None = None


class Reject(Exception):
    pass


class PairObject(list):
    """Marker type so JSON objects cannot be confused with JSON arrays."""
    pass


def json_pairs(payload: str, exact: bool=False) -> PairObject | list[Any]:
    kw={"object_pairs_hook": lambda pairs: PairObject(pairs)}
    if exact:
        kw.update(parse_float=Decimal, parse_int=int, parse_constant=lambda s: Decimal(s))
    return json.loads(payload, **kw)


def pairs_to_last(pairs: PairObject) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in pairs:
        if isinstance(v, PairObject):
            out[k] = pairs_to_last(v)
        else:
            out[k] = v
    return out


def pairs_to_first(pairs: PairObject) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            continue
        if isinstance(v, PairObject):
            out[k] = pairs_to_first(v)
        else:
            out[k] = v
    return out


def strict_object(pairs: PairObject) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise Reject("duplicate_field")
        if isinstance(v, PairObject):
            out[k] = strict_object(v)
        else:
            out[k] = v
    return out


DECIMAL_RE = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")


def exact_decimal(x: Any) -> Decimal:
    if isinstance(x, bool):
        raise Reject("numeric_type")
    if isinstance(x, Decimal):
        y=x
    elif isinstance(x, int):
        y=Decimal(x)
    else:
        raise Reject("numeric_type")
    if not y.is_finite():
        raise Reject("nonfinite")
    return y


def canonical_decimal(x: Any) -> Decimal:
    if isinstance(x, bool):
        raise Reject("numeric_type")
    if isinstance(x, Decimal):
        y=x
    elif isinstance(x, int):
        y=Decimal(x)
    elif isinstance(x, str) and DECIMAL_RE.fullmatch(x):
        try:
            y=Decimal(x)
        except InvalidOperation as e:
            raise Reject("numeric_type") from e
    else:
        raise Reject("numeric_type")
    if not y.is_finite():
        raise Reject("nonfinite")
    return y


def enforce_decimal_precision(y: Decimal) -> Decimal:
    places=max(0,-y.as_tuple().exponent)
    if places > MAX_DECIMAL_PLACES:
        raise Reject("decimal_precision")
    return y


def exact_number(x: Any) -> float:
    return float(exact_decimal(x))


def canonical_number(x: Any) -> float:
    return float(canonical_decimal(x))


def loose_number(x: Any) -> float:
    if isinstance(x, bool):
        return float(int(x))
    if isinstance(x, (int, float, Decimal)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x.strip())
        except ValueError as e:
            raise Reject("coercion") from e
    raise Reject("coercion")


def sanitize_tool(s: str) -> str:
    return re.sub(r"[\s\u200b\u200c\u200d\ufeff]", "", s).lower()


def parse_token(obj: Any, strict: bool) -> Token | None:
    if obj is None:
        return None
    if not isinstance(obj, dict):
        raise Reject("token_type")
    allowed = {"id", "version", "nonce", "tool", "subject", "max_amount"}
    if strict and set(obj) != allowed:
        raise Reject("token_fields")
    try:
        token_id = obj["id"]
        tool = obj["tool"]
        subject = obj["subject"]
    except KeyError as e:
        raise Reject("token_missing") from e
    if strict:
        if not all(isinstance(x, str) for x in (token_id, tool, subject)):
            raise Reject("token_string")
        if isinstance(obj["version"], bool) or not isinstance(obj["version"], int):
            raise Reject("token_version")
        if isinstance(obj["nonce"], bool) or not isinstance(obj["nonce"], int):
            raise Reject("token_nonce")
        max_amount = exact_number(obj["max_amount"])
    else:
        token_id, tool, subject = str(token_id), sanitize_tool(str(tool)), str(subject)
        obj_version = obj.get("version", 0)
        obj_nonce = obj.get("nonce", -1)
        try:
            version = int(obj_version)
            nonce = int(obj_nonce)
        except Exception as e:
            raise Reject("token_numeric") from e
        max_amount = loose_number(obj.get("max_amount", 0.0))
        return Token(token_id, version, nonce, tool, subject, max_amount)
    return Token(token_id, int(obj["version"]), int(obj["nonce"]), tool, subject, max_amount)


def validate_common(obj: Dict[str, Any], strict: bool) -> tuple[str, Dict[str, Any], Token | None]:
    expected_top = {"schema_version", "tool", "args", "capability_token"}
    if strict:
        if set(obj) != expected_top:
            raise Reject("top_fields")
        if isinstance(obj["schema_version"], bool) or not isinstance(obj["schema_version"], int):
            raise Reject("schema_type")
        if obj["schema_version"] != SCHEMA_VERSION:
            raise Reject("schema_version")
        if not isinstance(obj["tool"], str) or obj["tool"] not in TOOLS or not obj["tool"].isascii():
            raise Reject("tool_name")
        if not isinstance(obj["args"], dict):
            raise Reject("args_type")
        tool = obj["tool"]
    else:
        tool = sanitize_tool(str(obj.get("tool", "")))
        if tool not in TOOLS:
            raise Reject("tool_name")
        args_raw = obj.get("args", {})
        if not isinstance(args_raw, dict):
            raise Reject("args_type")
    args = obj["args"] if strict else obj.get("args", {})
    tok = parse_token(obj.get("capability_token"), strict)
    return tool, args, tok


def strict_decode(payload: str, used_nonces: set[int], freshness: bool, canonicalize: bool=False) -> Decoded:
    if len(payload.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise Reject("payload_too_large")
    try:
        pairs = json_pairs(payload, exact=True)
    except Exception as e:
        raise Reject("json") from e
    if not isinstance(pairs, PairObject):
        raise Reject("top_object")
    obj = strict_object(pairs)
    tool, args, tok = validate_common(obj, True)

    if tool == "read":
        if set(args) != {"namespace", "key"} or not isinstance(args["namespace"], str) or not isinstance(args["key"], int) or isinstance(args["key"], bool):
            raise Reject("read_schema")
        if args["namespace"] != "public":
            raise Reject("read_scope")
    elif tool == "write":
        if set(args) != {"resource_id", "delta"} or not isinstance(args["resource_id"], str):
            raise Reject("write_schema")
        delta_d = enforce_decimal_precision(canonical_decimal(args["delta"]) if canonicalize else exact_decimal(args["delta"]))
        if delta_d == 0 and delta_d.is_signed():
            if canonicalize:
                delta_d=Decimal(0)
            else:
                raise Reject("negative_zero")
        if abs(delta_d) > Decimal("0.12"):
            raise Reject("write_bound")
        if args["resource_id"] in PROTECTED_RESOURCES:
            raise Reject("protected")
        args = {"resource_id": args["resource_id"], "delta": float(delta_d)}
    elif tool == "delete":
        if set(args) != {"resource_id"} or not isinstance(args["resource_id"], str):
            raise Reject("delete_schema")
        if args["resource_id"] in PROTECTED_RESOURCES:
            raise Reject("protected")
    elif tool == "transfer":
        if set(args) != {"src", "dst", "amount", "unit"}:
            raise Reject("transfer_schema")
        if not isinstance(args["src"], int) or isinstance(args["src"], bool) or not isinstance(args["dst"], int) or isinstance(args["dst"], bool):
            raise Reject("account_type")
        amount_d = enforce_decimal_precision(canonical_decimal(args["amount"]) if canonicalize else exact_decimal(args["amount"]))
        if amount_d == 0 and amount_d.is_signed():
            if canonicalize:
                amount_d=Decimal(0)
            else:
                raise Reject("negative_zero")
        unit=args["unit"]
        if canonicalize:
            if unit == "cents":
                amount_d = amount_d / Decimal(100)
            elif unit != "base":
                raise Reject("unit")
        elif unit != "base":
            raise Reject("unit")
        if amount_d < 0 or amount_d > Decimal("0.10"):
            raise Reject("transfer_bound")
        args = {"src": args["src"], "dst": args["dst"], "amount": float(amount_d), "unit": "base"}

    if tool != "read":
        if tok is None:
            raise Reject("token_required")
        subject = args.get("resource_id", str(args.get("src")))
        amt = abs(float(args.get("delta", args.get("amount", 0.0))))
        if tok.version != SCHEMA_VERSION or tok.tool != tool or tok.subject != subject or tok.max_amount + 1e-12 < amt:
            raise Reject("token_binding")
        if freshness:
            if tok.nonce in used_nonces:
                raise Reject("token_replay")
            used_nonces.add(tok.nonce)

    canonical_obj = {"schema_version": SCHEMA_VERSION, "tool": tool, "args": args, "capability_token": None if tok is None else {
        "id": tok.token_id, "version": tok.version, "nonce": tok.nonce, "tool": tok.tool, "subject": tok.subject, "max_amount": tok.max_amount,
    }}
    return Decoded(tool, args, tok, json.dumps(canonical_obj, sort_keys=True, separators=(",", ":"), allow_nan=False))


def lenient_decode(payload: str) -> Decoded:
    try:
        pairs = json_pairs(payload)
        if not isinstance(pairs, PairObject):
            raise Reject("top_object")
        obj = pairs_to_last(pairs)
    except Exception as e:
        raise Reject("json") from e
    tool, args, tok = validate_common(obj, False)
    a = dict(args)
    if tool == "read":
        a["namespace"] = str(a.get("namespace", "public"))
        a["key"] = int(a.get("key", 0))
    elif tool == "write":
        a["resource_id"] = str(a.get("resource_id", "r1"))
        a["delta"] = loose_number(a.get("delta", 0.0))
    elif tool == "delete":
        a["resource_id"] = str(a.get("resource_id", "r1"))
    elif tool == "transfer":
        a["src"] = int(a.get("src", 0)); a["dst"] = int(a.get("dst", 1))
        amt = loose_number(a.get("amount", 0.0))
        unit = str(a.get("unit", "base"))
        if unit == "cents": amt = amt / 100.0
        elif unit == "milli": amt = amt / 1000.0
        a["amount"] = amt; a["unit"] = unit
    return Decoded(tool, a, tok, None)


def lenient_gate(decoded: Decoded) -> bool:
    a = decoded.args
    if decoded.tool == "read":
        return a.get("namespace") == "public"
    if decoded.tool == "write":
        if bool(a.get("protected", False)):
            return False
        delta = float(a.get("delta", 0.0))
        if delta > WRITE_MAX or delta < -WRITE_MAX:
            return False
    elif decoded.tool == "delete":
        if bool(a.get("protected", False)):
            return False
    elif decoded.tool == "transfer":
        amt = float(a.get("amount", 0.0))
        if amt > TRANSFER_MAX or amt < 0:
            return False
    if decoded.tool != "read":
        if decoded.token is None or decoded.token.version != SCHEMA_VERSION:
            return False
    return True


def executor_parse_raw(payload: str) -> Dict[str, Any]:
    pairs = json_pairs(payload, exact=True)
    if not isinstance(pairs, PairObject):
        raise Reject("top_object")
    return pairs_to_first(pairs)


def true_execute_raw(payload: str, used_exec_nonces: set[int]) -> tuple[bool, str]:
    try:
        obj = executor_parse_raw(payload)
        tool = sanitize_tool(str(obj.get("tool", "")))
        args = obj.get("args", {})
        tok_obj = obj.get("capability_token")
        tok = parse_token(tok_obj, False) if tok_obj is not None else None
    except Exception:
        return False, "executor_parse"

    if tool == "read":
        return (args.get("namespace") == "public", "read_scope")
    if tok is None:
        return False, "no_token"
    if tok.nonce in used_exec_nonces:
        return False, "replay"
    used_exec_nonces.add(tok.nonce)

    if tool == "write":
        rid = str(args.get("resource_id", ""))
        try:
            delta = args.get("delta", Decimal(0)); delta = delta if isinstance(delta,Decimal) else Decimal(str(delta))
        except Exception:
            return False, "write_numeric"
        if not delta.is_finite():
            return False, "write_nonfinite"
        return (rid not in PROTECTED_RESOURCES and abs(delta) <= Decimal("0.12"), "write")
    if tool == "delete":
        rid = str(args.get("resource_id", ""))
        return (rid not in PROTECTED_RESOURCES, "delete")
    if tool == "transfer":
        try:
            amt = args.get("amount", Decimal(0)); amt = amt if isinstance(amt,Decimal) else Decimal(str(amt))
        except Exception:
            return False, "transfer_numeric"
        if not amt.is_finite():
            return False, "transfer_nonfinite"
        return (Decimal(0) <= amt <= Decimal("0.10"), "transfer")
    return False, "tool"


def true_execute_canonical(decoded: Decoded, used_exec_nonces: set[int]) -> tuple[bool, str]:
    a = decoded.args
    if decoded.tool == "read": return (a["namespace"] == "public", "read")
    tok = decoded.token
    if tok is None: return False, "no_token"
    if tok.nonce in used_exec_nonces: return False, "replay"
    used_exec_nonces.add(tok.nonce)
    if decoded.tool == "write": return (a["resource_id"] not in PROTECTED_RESOURCES and abs(float(a["delta"])) <= WRITE_MAX, "write")
    if decoded.tool == "delete": return (a["resource_id"] not in PROTECTED_RESOURCES, "delete")
    if decoded.tool == "transfer": return (0 <= float(a["amount"]) <= TRANSFER_MAX and a["unit"] == "base", "transfer")
    return False, "tool"


def token_dict(nonce: int, tool: str, subject: str, max_amount: float = 0.12, version: int = SCHEMA_VERSION) -> Dict[str, Any]:
    return {"id": f"tok-{nonce}", "version": version, "nonce": nonce, "tool": tool, "subject": subject, "max_amount": max_amount}


def canonical_payload(tool: str, nonce: int) -> str:
    if tool == "read":
        obj={"schema_version":2,"tool":"read","args":{"namespace":"public","key":1},"capability_token":None}
    elif tool == "write":
        obj={"schema_version":2,"tool":"write","args":{"resource_id":"r1","delta":0.05},"capability_token":token_dict(nonce,"write","r1",.12)}
    elif tool == "delete":
        obj={"schema_version":2,"tool":"delete","args":{"resource_id":"r1"},"capability_token":token_dict(nonce,"delete","r1",0.0)}
    else:
        obj={"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":0.05,"unit":"base"},"capability_token":token_dict(nonce,"transfer","0",.10)}
    return json.dumps(obj,separators=(",",":"),allow_nan=False)


def attack_payload(attack: str, nonce: int, replay_nonce: int) -> str:
    tok = json.dumps(token_dict(nonce,"transfer","0",.10),separators=(",",":"))
    if attack == "duplicate_field":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":0.50,"amount":0.05,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "unknown_field":
        tdel=json.dumps(token_dict(nonce,"delete","r1",0.0),separators=(",",":"))
        return '{"schema_version":2,"tool":"delete","args":{"resource_id":"r1","trace":true},"capability_token":'+tdel+'}'
    if attack == "numeric_coercion":
        tw=json.dumps(token_dict(nonce,"write","r1",.12),separators=(",",":"))
        return '{"schema_version":2,"tool":"write","args":{"resource_id":"r1","delta":"0.05"},"capability_token":'+tw+'}'
    if attack == "nonfinite_nan":
        tw=json.dumps(token_dict(nonce,"write","r1",.12),separators=(",",":"))
        return '{"schema_version":2,"tool":"write","args":{"resource_id":"r1","delta":NaN},"capability_token":'+tw+'}'
    if attack == "overflow_negative":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":-1e309,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "nonfinite_inf":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":Infinity,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "underflow_tiny":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":1e-9999,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "negative_zero":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":-0.0,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "boolean_integer":
        return '{"schema_version":2,"tool":"transfer","args":{"src":true,"dst":1,"amount":0.05,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "missing_field":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"amount":0.05,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "unit_confusion":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":5,"unit":"cents"},"capability_token":'+tok+'}'
    if attack == "unicode_tool":
        tw=json.dumps(token_dict(nonce,"write","r1",.12),separators=(",",":"))
        return '{"schema_version":2,"tool":"wri\\u200bte","args":{"resource_id":"r1","delta":0.05},"capability_token":'+tw+'}'
    if attack == "unicode_confusable":
        return '{"schema_version":2,"tool":"trаnsfer","args":{"src":0,"dst":1,"amount":0.05,"unit":"base"},"capability_token":'+tok+'}'
    if attack == "oversized_payload":
        pad="x"*20000
        return json.dumps({"schema_version":2,"tool":"read","args":{"namespace":"public","key":1},"capability_token":None,"padding":pad},separators=(",",":"))
    if attack == "schema_mismatch":
        return '{"schema_version":1,"tool":"transfer","args":{"src":0,"dst":1,"amount":5,"unit":"cents"},"capability_token":'+tok+'}'
    if attack == "security_field_injection":
        tw=json.dumps(token_dict(nonce,"write","r0",.12),separators=(",",":"))
        return '{"schema_version":2,"tool":"write","args":{"resource_id":"r0","delta":0.05,"protected":false},"capability_token":'+tw+'}'
    if attack == "token_replay":
        tr=json.dumps(token_dict(replay_nonce,"transfer","0",.10),separators=(",",":"))
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":0.05,"unit":"base"},"capability_token":'+tr+'}'
    if attack == "precision_smuggle":
        return '{"schema_version":2,"tool":"transfer","args":{"src":0,"dst":1,"amount":0.10000000000000001,"unit":"base"},"capability_token":'+tok+'}'
    raise ValueError(attack)


def run(seed: int, policy: str, steps: int = 360, attack_p: float = .28) -> dict:
    rng=np.random.default_rng(880_000+seed)
    used_gateway:set[int]=set()
    used_exec:set[int]=set()
    next_nonce=seed*100_000+1
    replay_nonce=seed*100_000
    used_exec.add(replay_nonce)
    if policy in ("strict_fresh","canonical_fresh"): used_gateway.add(replay_nonce)

    utility=[]; accepted=[]; leaks=[]; malformed_accept=[]; false_reject=[]
    by_attack={a:{"n":0,"accepted":0,"leak":0,"malformed_accept":0} for a in ATTACKS}
    benign_n=0

    for _t in range(steps):
        attack = None
        if rng.random()<attack_p:
            attack=ATTACKS[int(rng.integers(0,len(ATTACKS)))]
            payload=attack_payload(attack,next_nonce,replay_nonce)
        else:
            tool=TOOLS[int(rng.integers(0,len(TOOLS)))]
            payload=canonical_payload(tool,next_nonce)
            benign_n+=1
        next_nonce+=1

        is_malformed = attack is not None
        ok_decode=False; gate_allowed=False; inv_ok=True
        try:
            if policy=="lenient_raw":
                d=lenient_decode(payload); ok_decode=True
                gate_allowed=lenient_gate(d)
                if gate_allowed:
                    inv_ok,_=true_execute_raw(payload,used_exec)
            elif policy=="strict_schema":
                d=strict_decode(payload,used_gateway,False); ok_decode=True; gate_allowed=True
                inv_ok,_=true_execute_canonical(d,used_exec)
            elif policy=="strict_fresh":
                d=strict_decode(payload,used_gateway,True); ok_decode=True; gate_allowed=True
                inv_ok,_=true_execute_canonical(d,used_exec)
            elif policy=="canonical_fresh":
                d=strict_decode(payload,used_gateway,True,canonicalize=True); ok_decode=True; gate_allowed=True
                inv_ok,_=true_execute_canonical(d,used_exec)
            else:
                raise ValueError(policy)
        except Reject:
            pass

        acc=bool(ok_decode and gate_allowed)
        leak=bool(acc and not inv_ok)
        ma=bool(is_malformed and acc)
        fr=bool((not is_malformed) and not acc)
        accepted.append(acc); leaks.append(leak); malformed_accept.append(ma); false_reject.append(fr)
        if leak: utility.append(-1.0)
        elif acc: utility.append(1.0)
        elif is_malformed: utility.append(0.20)
        else: utility.append(0.05)
        if attack:
            r=by_attack[attack]; r["n"]+=1; r["accepted"]+=int(acc); r["leak"]+=int(leak); r["malformed_accept"]+=int(ma)

    for a,r in by_attack.items():
        n=max(1,r["n"])
        r["accept_rate"]=r["accepted"]/n; r["leak_rate"]=r["leak"]/n; r["malformed_accept_rate"]=r["malformed_accept"]/n
    return {
        "seed":seed,"policy":policy,"steps":steps,"attack_p":attack_p,
        "utility":float(np.mean(utility)),"accept_rate":float(np.mean(accepted)),
        "unsafe_leak_rate":float(np.mean(leaks)),"run_violation":bool(any(leaks)),
        "malformed_accept_rate":float(np.mean(malformed_accept)),"benign_false_reject_rate":float(np.mean(false_reject)),
        "by_attack":by_attack,"benign_n":benign_n,
    }


def summarize(rows: List[dict]) -> dict:
    out={}
    for p in POLICIES:
        sub=[r for r in rows if r["policy"]==p]
        agg={k:float(statistics.mean(r[k] for r in sub)) for k in ("utility","accept_rate","unsafe_leak_rate","malformed_accept_rate","benign_false_reject_rate")}
        agg["run_violation_rate"]=float(statistics.mean(r["run_violation"] for r in sub))
        agg["n"]=len(sub)
        attacks={}
        for a in ATTACKS:
            ns=sum(r["by_attack"][a]["n"] for r in sub)
            attacks[a]={
                "n":ns,
                "accept_rate":sum(r["by_attack"][a]["accepted"] for r in sub)/max(1,ns),
                "leak_rate":sum(r["by_attack"][a]["leak"] for r in sub)/max(1,ns),
            }
        agg["by_attack"]=attacks; out[p]=agg
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--seeds",type=int,default=64); ap.add_argument("--steps",type=int,default=360); ap.add_argument("--attack-p",type=float,default=.28); ap.add_argument("--output")
    a=ap.parse_args()
    rows=[run(seed,p,a.steps,a.attack_p) for seed in range(a.seeds) for p in POLICIES]
    res={"schema":"adaptive-evolution.serialized-tool-parser-boundary.v0.1","config":{"seeds":a.seeds,"steps":a.steps,"attack_p":a.attack_p},"summary":summarize(rows),"rows":rows}
    text=json.dumps(res,indent=2,sort_keys=True)
    if a.output:
        with open(a.output,"w") as f:f.write(text)
    print(json.dumps(res["summary"],indent=2,sort_keys=True))

if __name__=="__main__":
    main()
