"""Conservative, opt-in compaction at advertising Agent input boundaries."""
import hashlib
import json
from pathlib import Path
import re


def optimize_ad_inputs(messages, state, node_id):
    if state.get('ad_context_policy') != 'file_first_v1':
        return messages, None
    receipts = state.get('ad_artifact_receipts', {})
    if not state.get('python_workspace_root'):
        return messages, None
    root = Path(state['python_workspace_root']).resolve()
    before = sum(len(message.text_content()) for message in messages)
    result, seen = [], set()
    duplicates = elisions = 0
    protected = {'Director_Brief', 'Strategy_QA'}
    for message in messages:
        source = message.metadata.get('source')
        # Never touch decisions/questions, attachments, or tool-call/result pairs.
        eligible = (isinstance(source, str) and source in receipts and source not in protected and isinstance(message.content, str)
                    and not message.tool_call_id and not message.tool_calls
                    and str(message.role.value) in ('user', 'assistant'))
        if not eligible:
            result.append(message)
            continue
        text = message.text_content()
        key = (source, str(message.role), text, json.dumps(message.metadata, sort_keys=True, default=str))
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        for name, digest in receipts[source].items():
            path = root / 'artifacts' / name
            try:
                if not path.resolve().is_relative_to(root) or not path.is_file():
                    continue
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != digest:
                    continue  # Source changed since the validated handoff; don't hide old context.
                body = data.decode('utf-8-sig').replace('\r\n', '\n').strip()
            except (OSError, UnicodeError):
                continue  # Optional compaction must not fail a run or hide unreadable inputs.
            if len(body) < 500:
                continue
            marker = '[Nội dung file đã kiểm tra: artifacts/' + name + '; dùng load_file để đọc bản hiện hành.]'
            def replace_fence(match):
                nonlocal elisions
                if match.group(1).replace('\r\n', '\n').strip() == body:
                    elisions += 1
                    return marker
                return match.group(0)
            text = re.sub(r'```[^\n]*\n(.*?)\n```', replace_fence, text, flags=re.S)
            # A verbatim Markdown handoff may not be fenced. Keep all surrounding commentary.
            if body in text:
                text = text.replace(body, marker)
                elisions += 1
        result.append(message.with_content(text))
    stats = {'node_id': node_id, 'policy': 'file_first_v1', 'input_characters_before': before,
             'input_characters_after': sum(len(message.text_content()) for message in result),
             'duplicate_handoffs_removed': duplicates, 'verbatim_artifacts_replaced': elisions,
             'note': 'Character counts at Agent input, not billed tokens or measured model quality.'}
    return result, stats
