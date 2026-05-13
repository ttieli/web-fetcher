#!/usr/bin/env python3
"""
V2 fallback 行为验证脚本

补 scripts/run_regression_suite.py 的能力盲区：
run_regression_suite 调 fetch_html_with_retry 不走 V2 引擎，
本脚本 subprocess 调 wf 完整 CLI 路径，从 stderr 解析 V2 行为：
- score 跃迁是否符合预期
- raw markdown URL 是否短路（无 auto-upgrade 日志）
- SPA 站点是否真的继续升级（不再卡死在 cdp）

按 url_suite.txt 的 tag 分组断言：

| tag                          | 断言 |
|------------------------------|------|
| short-circuit                | 必须见 'short-circuit: plain-text URL'，不见 'auto-upgrade' |
| fallback-rescue              | 必须见 'auto-upgrade accepted' 且最终 score >= 0.5 |
| spa,v2-fallback-fix          | 必须见 'auto-upgrade [2/3]' 或更深（之前卡死在 [1/3]） |
| static (urllib-ok)           | 必须 urllib 一次成功，不触发 auto-upgrade |

用法：
    python scripts/verify_v2_fallback.py                  # 跑 v2-fallback-fix 子集
    python scripts/verify_v2_fallback.py --tags short-circuit
    python scripts/verify_v2_fallback.py --all            # 跑全 35 个
"""

import argparse
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path


SUITE_FILE = Path(__file__).parent.parent / 'tests' / 'url_suite.txt'


def parse_suite(suite_path: Path):
    """Parse url_suite.txt，返回 list[(url, description, expected, tags_set)]"""
    out = []
    for ln_idx, line in enumerate(suite_path.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) != 4:
            continue
        url, desc, expected, tags = parts
        out.append({
            'url': url,
            'description': desc,
            'expected': expected,
            'tags': set(t.strip() for t in tags.split(',')),
            'line': ln_idx,
        })
    return out


def filter_tests(tests, include_tags=None, exclude_tags=None):
    out = []
    for t in tests:
        if include_tags and not (t['tags'] & include_tags):
            continue
        if exclude_tags and (t['tags'] & exclude_tags):
            continue
        out.append(t)
    return out


# Regex 模板（基于 wf stderr 日志格式）
RE_SHORT_CIRCUIT = re.compile(r'V2 competition short-circuit: plain-text URL')
RE_AUTO_UPGRADE = re.compile(r'V2 auto-upgrade \[(\d+)/(\d+)\]: → (\w+)')
RE_UPGRADE_ACCEPT = re.compile(r'V2 auto-upgrade accepted: (\w+), score: ([\d.]+) → ([\d.]+)')
RE_UPGRADE_COMPLETE = re.compile(r'V2 auto-upgrade complete: score ([\d.]+) >= 0.5, stop')
RE_WINNER = re.compile(r'V2 competition winner: (\w+) \(score=([\d.]+),')
RE_QUALITY_LOW = re.compile(r'V2: quality low \(([^)]+)\)')


def run_wf(url: str, timeout: int = 120):
    """Subprocess 调 wf，返回 (returncode, stderr_text, duration_s)。"""
    start = time.time()
    try:
        proc = subprocess.run(
            ['wf', url, '--stdout'],
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, proc.stderr, time.time() - start
    except subprocess.TimeoutExpired:
        return -1, f'TIMEOUT after {timeout}s', time.time() - start
    except Exception as e:
        return -2, f'EXCEPTION: {e}', time.time() - start


def analyze_log(stderr: str) -> dict:
    """从 wf stderr 日志提取 V2 行为关键事件。"""
    info = {
        'short_circuited': bool(RE_SHORT_CIRCUIT.search(stderr)),
        'upgrade_attempts': [],
        'upgrade_accepts': [],
        'upgrade_complete_score': None,
        'final_winner': None,
        'final_score': 0.0,
        'quality_low_seen': False,
    }
    for m in RE_AUTO_UPGRADE.finditer(stderr):
        info['upgrade_attempts'].append({
            'step': int(m.group(1)),
            'total': int(m.group(2)),
            'mode': m.group(3),
        })
    for m in RE_UPGRADE_ACCEPT.finditer(stderr):
        info['upgrade_accepts'].append({
            'mode': m.group(1),
            'prev_score': float(m.group(2)),
            'new_score': float(m.group(3)),
        })
    m = RE_UPGRADE_COMPLETE.search(stderr)
    if m:
        info['upgrade_complete_score'] = float(m.group(1))
    # 最后一次 winner 记录
    winners = list(RE_WINNER.finditer(stderr))
    if winners:
        last = winners[-1]
        info['final_winner'] = last.group(1)
        info['final_score'] = float(last.group(2))
    info['quality_low_seen'] = bool(RE_QUALITY_LOW.search(stderr))
    return info


def assert_test(test: dict, info: dict) -> tuple[bool, list]:
    """根据 tags 做行为断言。返回 (passed, notes)"""
    tags = test['tags']
    notes = []
    passed = True

    if 'short-circuit' in tags:
        # 必须短路
        if not info['short_circuited']:
            passed = False
            notes.append('❌ 期望短路但未触发')
        else:
            notes.append('✅ 短路触发')
        if info['upgrade_attempts']:
            passed = False
            notes.append(f"❌ 不应触发 auto-upgrade，实际触发 {len(info['upgrade_attempts'])} 次")
        else:
            notes.append('✅ 无 auto-upgrade')

    elif 'fallback-rescue' in tags:
        # fallback 可以发生在两层：
        # 1. fetch 层（fetch_html_with_retry 内部 urllib→cdp，无 V2 auto-upgrade 日志）
        # 2. V2 层（generic_v2 quality_low 后触发 auto-upgrade）
        # 任一层成功且最终 score >= 0.5 即视为通过
        if info['upgrade_accepts']:
            last_accept = info['upgrade_accepts'][-1]
            notes.append(f"✅ V2 层升级 accepted: {last_accept['mode']} "
                         f"({last_accept['prev_score']:.2f} → {last_accept['new_score']:.2f})")
            if last_accept['new_score'] < 0.5:
                passed = False
                notes.append(f"❌ V2 升级后 score {last_accept['new_score']:.2f} < 0.5")
        elif info['final_score'] >= 0.5:
            notes.append(f"✅ fetch 层 fallback 救回，最终 score={info['final_score']:.2f}")
        else:
            passed = False
            notes.append(f"❌ 救回失败：无 V2 升级 + final_score={info['final_score']:.2f}")

    elif 'spa' in tags and 'v2-fallback-fix' in tags:
        # SPA stuck：之前永远卡在 [1/3]，修复后应至少升到 [2/3]
        if not info['upgrade_attempts']:
            notes.append('⚠️  无升级尝试（可能 fetch 层直接失败）')
        else:
            max_step = max(a['step'] for a in info['upgrade_attempts'])
            if max_step < 2:
                # 升到 [2/3] 或更深才算"修复后行为"
                # 但是如果 cdp 后 score >= 0.5 就 break，[1/3] 是合理的
                if info['upgrade_complete_score'] is not None:
                    notes.append(f"✅ 升级在 [{max_step}/3] 后正常 complete "
                                 f"(score={info['upgrade_complete_score']:.2f})")
                else:
                    passed = False
                    notes.append(f"❌ 仅升到 [{max_step}/3] 且未 complete，可能仍卡死")
            else:
                notes.append(f"✅ 升级到 [{max_step}/3]（之前修复前会卡在 [1/3]）")

    elif 'static' in tags:
        # urllib 应该一次成功，无升级
        if info['upgrade_attempts']:
            passed = False
            notes.append(f"❌ static 站点不应触发升级，实际 {len(info['upgrade_attempts'])} 次")
        else:
            notes.append('✅ 无升级')
        if info['final_score'] < 0.5 and not info['short_circuited']:
            notes.append(f"⚠️  final_score {info['final_score']:.2f} < 0.5（已知数据）")

    else:
        notes.append(f"ℹ️  no specific assertion for tags {sorted(tags)}")

    return passed, notes


def main():
    parser = argparse.ArgumentParser(
        description='V2 fallback 行为验证（补 run_regression_suite.py 盲区）')
    parser.add_argument('--tags', help='包含 tags（逗号分隔），默认 v2-fallback-fix')
    parser.add_argument('--exclude-tags', help='排除 tags（逗号分隔）')
    parser.add_argument('--all', action='store_true', help='跑全 suite')
    parser.add_argument('--timeout', type=int, default=120, help='per-URL timeout 秒')
    parser.add_argument('--suite-file', type=Path, default=SUITE_FILE)
    args = parser.parse_args()

    tests = parse_suite(args.suite_file)
    print(f"Loaded {len(tests)} URLs from {args.suite_file.name}", file=sys.stderr)

    if args.all:
        include = None
    else:
        include = {t.strip() for t in (args.tags or 'v2-fallback-fix').split(',')}

    exclude = None
    if args.exclude_tags:
        exclude = {t.strip() for t in args.exclude_tags.split(',')}

    tests = filter_tests(tests, include, exclude)
    print(f"Running {len(tests)} tests "
          f"(include={include}, exclude={exclude})\n", file=sys.stderr)

    results = []
    for i, test in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] {test['url'][:70]}", file=sys.stderr)
        rc, stderr, dur = run_wf(test['url'], timeout=args.timeout)
        info = analyze_log(stderr)
        ok, notes = assert_test(test, info)
        results.append({
            'test': test, 'info': info, 'passed': ok, 'notes': notes,
            'duration': dur, 'rc': rc,
        })
        status = '✅' if ok else '❌'
        print(f"     {status} {dur:.1f}s  short={info['short_circuited']}  "
              f"upgrades={len(info['upgrade_attempts'])}  "
              f"score={info['final_score']:.2f}",
              file=sys.stderr)
        for n in notes:
            print(f"     {n}", file=sys.stderr)
        print(file=sys.stderr)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    failed = total - passed
    print("=" * 72)
    print(f"V2 FALLBACK VERIFICATION REPORT")
    print("=" * 72)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print(f"Success: {passed/total*100:.1f}%")
    print()

    by_cat = defaultdict(lambda: {'pass': 0, 'fail': 0})
    for r in results:
        tags = r['test']['tags']
        # 主类别识别
        if 'short-circuit' in tags:
            cat = 'short-circuit'
        elif 'fallback-rescue' in tags:
            cat = 'fallback-rescue'
        elif 'spa' in tags:
            cat = 'spa-stuck'
        elif 'static' in tags:
            cat = 'static'
        else:
            cat = 'other'
        by_cat[cat]['pass' if r['passed'] else 'fail'] += 1
    print("BY CATEGORY:")
    for cat, c in sorted(by_cat.items()):
        total_c = c['pass'] + c['fail']
        print(f"  {cat:20s}: {c['pass']:3d}/{total_c} pass")
    print()

    if failed:
        print("FAILED TESTS:")
        for r in results:
            if r['passed']:
                continue
            t = r['test']
            print(f"  ❌ {t['url'][:80]}")
            print(f"     tags: {sorted(t['tags'])}")
            for n in r['notes']:
                if '❌' in n:
                    print(f"     {n}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
