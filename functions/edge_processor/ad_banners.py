"""One Python banner node, activated only by the checked plan approval edge."""
import json
from pathlib import Path

from functions.edge_processor.ad_agency_routes import ad_checked_payload


def ad_banner_script(data, context):
    checked=ad_checked_payload(data,context)
    if checked is None or not str(checked).rstrip().endswith('[[REVIEW_APPROVE]]'):
        return None
    repo=str(Path(__file__).resolve().parents[2])
    return ('import json, os, pathlib, sys\n'
            'sys.path.insert(0, '+repr(repo)+')\n'
            'from utils.ad_banner import produce_banners\n'
            'try:\n'
            '    result = produce_banners(os.environ["MAC_CODE_WORKSPACE"])\n'
            '    print(json.dumps(result, ensure_ascii=False))\n'
            '    print("[[BANNER_READY]]")\n'
            'except Exception as exc:\n'
            '    root = pathlib.Path(os.environ["MAC_CODE_WORKSPACE"])\n'
            '    folder = root / "internal"\n'
            '    if folder.is_dir() and folder.resolve().is_relative_to(root.resolve()):\n'
            '        reason = str(exc) if isinstance(exc, (ValueError, KeyError, FileExistsError)) else "See exception type; upstream response/credentials omitted."\n'
            '        (folder / "banner_error.json").write_text(json.dumps({"status":"ERROR", "exception":type(exc).__name__, "reason":reason, "notice":"Check configuration, source integrity and request ledger before retry. No automatic retry."}), encoding="utf-8")\n'
            '    print("[[EXEC_FAIL]]")\n'
            '    print("Banner_Producer failed (" + type(exc).__name__ + "); no complete banner handoff. See internal/banner_error.json and request ledger.")\n')


def ad_banner_result(data, context):
    text=str(data or '').strip()
    if '[[EXEC_FAIL]]' in text or not text.endswith('\n[[BANNER_READY]]'):
        return None
    try:
        obj=json.loads(text.rsplit('\n',1)[0])
        assets=obj['assets']
        if not isinstance(assets,list):
            return None
        if obj['status']=='CREATED' and not 1 <= len(assets) <= 4:
            return None
        if obj['status']=='DISABLED' and assets:
            return None
        if obj['status'] not in ('CREATED','DISABLED'):
            return None
    except (ValueError,KeyError,TypeError):
        return None
    return text


def ad_banner_fallback(data, context):
    if ad_banner_result(data,context) is not None:
        return None
    return '[[EXEC_FAIL]]\nBanner_Producer did not return a complete, valid image handoff. Check internal/banner_error.json.'
