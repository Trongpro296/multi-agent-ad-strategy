"""Offline checks before paying for an advertising workflow run.

Usage: uv run python tools/preflight_ad_agency.py
       uv run python tools/preflight_ad_agency.py --all-yamls
Never creates an API client, runs a workflow, or sends a model request.
"""
import argparse
import contextlib
import io
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def check_chat_file_delivery():
    """No SDK client: ensure text attachments survive Chat tool serialization."""
    import tempfile
    from entity.configs.node.agent import AgentConfig
    from entity.messages import AttachmentRef,Message,MessageBlock,MessageBlockType,MessageRole
    from runtime.node.agent.providers.openai_provider import OpenAIProvider
    config=AgentConfig(path='preflight',name='offline',provider='openai',base_url=None,api_key='offline',params={'protocol':'chat'})
    provider=OpenAIProvider(config)
    with tempfile.TemporaryDirectory(prefix='chat_file_preflight_') as folder:
        for filename,mime,text in (
            ('probe.md','text/markdown','PREFLIGHT_MARKDOWN_TEXT'),
            ('probe.json','application/json','{"check":"PREFLIGHT_JSON_TEXT"}'),
            ('probe.csv','application/vnd.ms-excel','id,value\n1,PREFLIGHT_CSV_TEXT\n'),
        ):
            path=Path(folder)/filename;path.write_text(text,encoding='utf-8-sig',newline='\n')
            block=MessageBlock(MessageBlockType.FILE,attachment=AttachmentRef(attachment_id='probe',name=filename,mime_type=mime,local_path=str(path)))
            message=Message(role=MessageRole.TOOL,content=[block],tool_call_id='offline-probe')
            payload=provider._build_chat_payload([message],None,{})
            if text not in payload['messages'][0]['content']:
                raise ValueError('Chat tool attachment content missing: '+filename)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all-yamls',action='store_true',help='Also validate all bundled examples statically')
    parser.add_argument('--auto',action='store_true',help='Also require the benchmark auto variant to be runnable')
    args=parser.parse_args()
    os.chdir(ROOT)
    from utils.env_loader import load_dotenv_file
    load_dotenv_file()
    from runtime import sdk
    from check.check import load_config,check_config
    from entity.configs.node.agent import AgentConfig
    from runtime.node.agent.skills import AgentSkillManager
    from utils.function_manager import get_function_manager,EDGE_PROCESSOR_FUNCTION_DIR,FUNCTION_CALLING_DIR
    from utils.code_execution import require_unsafe_code_execution
    import yaml
    from importlib import import_module
    problems=[]
    try:
        check_chat_file_delivery()
        print('OK Chat tool file content: Markdown / JSON / CSV (offline)')
    except Exception as exc:
        problems.append('Chat tool file content check failed: '+type(exc).__name__)
    for module in ('openpyxl','pptx'):
        try: import_module(module);print('OK dependency:',module)
        except Exception as exc: problems.append('dependency '+module+': '+type(exc).__name__)
    try:require_unsafe_code_execution('Advertising Python nodes');print('OK Python execution flag')
    except Exception:problems.append('Set MAC_ALLOW_UNSAFE_CODE_EXECUTION=1 in the backend environment, then restart backend')
    processors=get_function_manager(EDGE_PROCESSOR_FUNCTION_DIR)
    functions=get_function_manager(FUNCTION_CALLING_DIR)
    filenames=('ad_agency_v2.yaml','ad_agency_v2_auto.yaml') if args.auto else ('ad_agency_v2.yaml',)
    for filename in filenames:
        path=ROOT/'yaml_instance'/filename
        try:
            if filename.endswith('_auto.yaml'):
                missing=[key for key in ('MODEL_STRONG','MODEL_CHEAP','MODEL_REVIEW') if not os.environ.get(key)]
                if missing:
                    problems.append(filename+': configure '+', '.join(missing)+' in .env before using benchmark auto')
                    continue
            with contextlib.redirect_stdout(io.StringIO()):config=load_config(path)
            raw=yaml.safe_load(path.read_text(encoding='utf-8'))['graph']
            skill_count=0
            for edge in raw['edges']:
                proc=edge.get('process',{})
                if proc.get('type')=='function' and processors.get_function(proc['config']['name']) is None:
                    problems.append(filename+': missing edge processor '+proc['config']['name'])
            for node in config.graph.nodes:
                agent=node.as_config(AgentConfig)
                if not agent:continue
                if not agent.base_url or not agent.api_key:
                    problems.append(filename+': missing model endpoint/key for '+node.id)
                if not agent.tooling:
                    problems.append(filename+': missing tools for '+node.id)
                if agent.provider.lower()=='openai' and (agent.params or {}).get('protocol')!='chat':
                    problems.append(filename+': this advertising gateway workflow requires explicit protocol=chat at '+node.id)
                for toolgroup in agent.tooling:
                    if toolgroup.type!='function':continue
                    for entry in toolgroup.config.tools:
                        if functions.get_function(entry['name']) is None:
                            problems.append(filename+': tool unavailable '+entry['name']+' at '+node.id)
                if agent.skills and agent.skills.enabled:
                    manager=AgentSkillManager(allow=agent.skills.allow)
                    found={skill.name for skill in manager.discover()}
                    if not agent.skills.allow or found!=set(agent.skills.allow) or manager.discovery_warnings():
                        problems.append(filename+': invalid or missing skill allowlist for '+node.id)
                    else:
                        for name in agent.skills.allow:manager.activate_skill(name)
                        skill_count+=1
            print('OK loaded schema/graph:',filename,len(config.graph.nodes),'nodes')
            print('OK local skill discovery/activation:',skill_count,'agents')
        except Exception as exc:
            # Do not print config dumps, provider URLs, keys or environment values.
            problems.append(filename+': '+type(exc).__name__+' (invalid configuration; inspect locally)')
    if args.all_yamls:
        files=list((ROOT/'yaml_instance').rglob('*.yaml'));ok=0
        for path in files:
            try:
                error=check_config(yaml.safe_load(path.read_text(encoding='utf-8')))
                if error:problems.append('example schema/graph invalid: '+str(path.relative_to(ROOT)))
                else:ok+=1
            except Exception as exc:problems.append(str(path.relative_to(ROOT))+': '+type(exc).__name__)
        print('Static YAML validation:',ok,'/',len(files))
    for problem in problems:print('FAIL:',problem)
    print('PREFLIGHT:', 'FAILED' if problems else 'OK','(offline; model availability and generation quality not tested)')
    return bool(problems)


if __name__=='__main__':
    raise SystemExit(main())
