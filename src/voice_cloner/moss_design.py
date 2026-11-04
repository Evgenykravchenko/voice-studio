"""Load the pinned author's processor without leaking download options into its constructor."""


def load_processor(path, codec):
    from transformers.dynamic_module_utils import get_class_from_dynamic_module
    # The author's from_pretrained forwards all remaining kwargs to ProcessorMixin,
    # which rejects local_files_only. Resolve the reviewed local class first;
    # its nested config/tokenizer/codec loaders remain guarded by local_resources.
    processor_class = get_class_from_dynamic_module(
        'processing_moss_tts.MossTTSDelayProcessor', str(path), local_files_only=True,
    )
    return processor_class.from_pretrained(
        str(path), codec_path=str(codec), normalize_inputs=False,
    )
