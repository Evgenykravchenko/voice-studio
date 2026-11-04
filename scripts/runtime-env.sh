# Source after PROJECT_ROOT has been resolved by the calling script.
export UV_CACHE_DIR="$PROJECT_ROOT/.runtime/cache/uv"
export UV_PYTHON_INSTALL_DIR="$PROJECT_ROOT/.runtime/python"
export UV_PYTHON_BIN_DIR="$PROJECT_ROOT/.runtime/bin"
export UV_TOOL_DIR="$PROJECT_ROOT/.runtime/uv-tools"
export UV_NO_MODIFY_PATH=1
# Large wheels must survive a temporarily slow connection on first installation.
export UV_HTTP_TIMEOUT="${UV_HTTP_TIMEOUT:-300}"
export UV_HTTP_RETRIES="${UV_HTTP_RETRIES:-5}"
export XDG_CACHE_HOME="$PROJECT_ROOT/.runtime/cache"
export HF_HOME="$PROJECT_ROOT/.runtime/cache/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HUB_CACHE"
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TORCH_HOME="$PROJECT_ROOT/.runtime/cache/torch"
export MPLCONFIGDIR="$PROJECT_ROOT/.runtime/cache/matplotlib"
export NUMBA_CACHE_DIR="$PROJECT_ROOT/.runtime/cache/numba"
export PYTHONPYCACHEPREFIX="$PROJECT_ROOT/.runtime/pycache"
export npm_config_cache="$PROJECT_ROOT/.runtime/cache/npm"
export npm_config_userconfig=/dev/null
export npm_config_globalconfig=/dev/null
export npm_config_fund=false
export npm_config_audit=false
if [ -x "$PROJECT_ROOT/.runtime/toolchains/node/bin/node" ]; then
  PATH="$PROJECT_ROOT/.runtime/toolchains/node/bin:$PATH"
fi
if [ -x "$PROJECT_ROOT/.runtime/toolchains/java/Contents/Home/bin/java" ]; then
  JAVA_HOME="$PROJECT_ROOT/.runtime/toolchains/java/Contents/Home"
  export JAVA_HOME
fi
PATH="$PROJECT_ROOT/.runtime/bin:$PATH"
export PATH
