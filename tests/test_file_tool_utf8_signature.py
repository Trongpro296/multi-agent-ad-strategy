"""Prevent model-supplied BOMs from corrupting real CSV header contracts."""
import codecs
import csv
import io

import pytest

from runtime import sdk
from entity.messages import Message, MessageRole
from functions.function_calling.file import save_file
from functions.edge_processor.ad_agency_contracts import _validate_result
from utils.attachments import AttachmentStore
from utils.exceptions import WorkflowExecutionError


def context(root):
    return {'python_workspace_root': root, 'graph_directory': root.parent,
            'attachment_store': AttachmentStore(root / 'attachments')}


@pytest.mark.parametrize('encoding', ['utf-8-sig', 'UTF_8_SIG'])
@pytest.mark.parametrize('prefix_count', [0, 1, 2])
def test_overwrite_normalizes_signature_and_passes_evidence_contract(tmp_path, encoding, prefix_count):
    state = context(tmp_path)
    text = 'id,claim,source_url,access_date,scope,evidence_type\nS1,Giả thuyết cần xác minh,,,brief,hypothesis\n'
    result = save_file('artifacts/sources.csv', '\ufeff' * prefix_count + text,
                       encoding=encoding, _context=state)
    data = (tmp_path / 'artifacts/sources.csv').read_bytes()
    assert data == codecs.BOM_UTF8 + text.encode('utf-8')
    assert result['size'] == len(data)
    assert list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))[0]['id'] == 'S1'
    save_file('artifacts/evidence_digest.md', '# Giới hạn\nChưa có bằng chứng ngoài.', _context=state)
    _validate_result('Evidence_Digest', Message(role=MessageRole.ASSISTANT, content='Đã lưu hai file.'), state)


@pytest.mark.parametrize('initial', [None, b'', codecs.BOM_UTF8 + b'id,claim\n', b'id,claim\n'])
def test_append_only_emits_signature_at_start_of_new_or_empty_file(tmp_path, initial):
    state = context(tmp_path)
    target = tmp_path / 'table.csv'
    if initial is not None:
        target.write_bytes(initial)
    text = 'S1,Tiếng Việt\n'
    save_file('table.csv', '\ufeff\ufeff' + text, encoding='utf-8-sig', mode='append', _context=state)
    expected = (initial if initial else codecs.BOM_UTF8) + text.encode('utf-8')
    assert target.read_bytes() == expected


def test_plain_utf8_and_internal_bom_remain_unchanged(tmp_path):
    state = context(tmp_path)
    text = '\ufeffđầu\ufeffgiữa'
    save_file('plain.txt', text, encoding='utf-8', _context=state)
    assert (tmp_path / 'plain.txt').read_bytes() == text.encode('utf-8')
    save_file('signature.txt', text, encoding='utf-8-sig', _context=state)
    assert (tmp_path / 'signature.txt').read_bytes() == text.encode('utf-8')


def test_bom_normalization_does_not_accept_wrong_csv_columns(tmp_path):
    state = context(tmp_path)
    save_file('artifacts/evidence_digest.md', '# Báo cáo', _context=state)
    save_file('artifacts/sources.csv', '\ufeffwrong,claim\nS1,Nhận định\n', encoding='utf-8-sig', _context=state)
    with pytest.raises(WorkflowExecutionError, match='CSV columns invalid sources.csv'):
        _validate_result('Evidence_Digest', Message(role=MessageRole.ASSISTANT, content='Đã lưu.'), state)
