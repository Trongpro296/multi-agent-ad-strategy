"""Compare local token_usage JSON files; no model calls or price assumptions."""
import argparse
import json
from pathlib import Path


def compare_runs(before, after):
    for value in (before, after):
        if not isinstance(value, dict) or not isinstance(value.get('total_usage'), dict):
            raise ValueError('Expected a token_usage JSON object with total_usage')
    totals = {}
    for key in ('input_tokens', 'output_tokens', 'total_tokens'):
        old, new = before['total_usage'].get(key), after['total_usage'].get(key)
        if not isinstance(old, int) or not isinstance(new, int) or old < 0 or new < 0:
            raise ValueError('Missing/invalid provider-reported token count: ' + key)
        totals[key] = {'before': old, 'after': new, 'change': new - old,
                       'change_pct': round((new - old) * 100 / old, 2) if old else None}
    nodes = []
    for name in sorted(set(before.get('node_usages', {})) | set(after.get('node_usages', {}))):
        old = before.get('node_usages', {}).get(name, {}).get('total_tokens', 0)
        new = after.get('node_usages', {}).get(name, {}).get('total_tokens', 0)
        nodes.append({'node': name, 'before_tokens': old, 'after_tokens': new, 'change': new - old})
    return {'totals': totals,
            'model_calls': {'before': len(before.get('call_history', [])), 'after': len(after.get('call_history', []))},
            'models_changed': set(before.get('model_usages', {})) != set(after.get('model_usages', {})),
            'nodes': nodes, 'after_context_optimizations': after.get('context_optimizations', []),
            'limits': 'Compare the same brief, model/configuration and review outcome. Counts include tool-loop calls; provider tokens are not a price estimate. Offline character savings do not establish quality or live token savings.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', required=True, type=Path)
    parser.add_argument('--after', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(compare_runs(json.loads(args.before.read_text(encoding='utf-8-sig')),
                                  json.loads(args.after.read_text(encoding='utf-8-sig'))), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
