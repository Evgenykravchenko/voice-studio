"""Resolve third-party codec/tokenizer lookups to this model's pinned local bundle."""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from .models import snapshot, file_path


@contextmanager
def local_resources(model):
    # Piper loads pinned ONNX/JSON files directly and has no Hugging Face dependency.
    if model.get("adapter") == "piper":
        yield
        return
    import huggingface_hub as hub
    locations = {model['repo']: snapshot(model)}
    files = {}
    for item in model['files']:
        repo = item.get('repo', model['repo'])
        files[(repo, item['path'])] = file_path(model, item)
        locations[repo] = snapshot({'repo': repo, 'revision': item.get('revision',model['revision'])})
    def download(repo_id, filename, *args, **kwargs):
        repo_id=model.get('resourceAliases',{}).get(repo_id,repo_id)
        path = files.get((repo_id,filename))
        if path is None or not path.is_file():
            raise FileNotFoundError(f'В установленном комплекте отсутствует {repo_id}/{filename}. Повторите установку модели.')
        return str(path)
    def repository(repo_id, *args, **kwargs):
        path = locations.get(repo_id)
        if path is None:
            raise FileNotFoundError(f'Зависимость {repo_id} не входит в комплект модели. Обновите каталог студии.')
        return str(path)
    for alias,repo in model.get('resourceAliases',{}).items():
        if repo in locations: locations[alias]=locations[repo]
    # Patches are scoped to the isolated child process. Unknown downloads fail offline.
    with patch.object(hub,'hf_hub_download',download), patch.object(hub,'snapshot_download',repository):
        from contextlib import ExitStack
        patches = []
        torch_available=False
        try:
            from transformers import AutoTokenizer, AutoProcessor, AutoFeatureExtractor, AutoConfig
            from transformers.utils import is_torch_available
        except ImportError:
            classes = []
        else:
            classes = [AutoTokenizer, AutoProcessor, AutoFeatureExtractor, AutoConfig]
            torch_available=is_torch_available()
            if torch_available:
                from transformers import AutoModel, PreTrainedModel
                classes.append(AutoModel)
        if torch_available:
            original_model_loader=PreTrainedModel.from_pretrained.__func__
            def local_model_loader(cls,path,*args,**kwargs):
                path=locations.get(str(path),path)
                kwargs['local_files_only']=True
                return original_model_loader(cls,path,*args,**kwargs)
            patches.append(patch.object(PreTrainedModel,'from_pretrained',classmethod(local_model_loader)))
        for cls in classes:
            original = cls.from_pretrained
            def local_loader(path, *args, _original=original, **kwargs):
                path = locations.get(str(path), path)
                kwargs['local_files_only'] = True
                return _original(path,*args,**kwargs)
            patches.append(patch.object(cls,'from_pretrained',local_loader))
        with ExitStack() as stack:
            for item in patches: stack.enter_context(item)
            yield
