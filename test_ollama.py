import ollama

# Fetch model list from Ollama
models_info = ollama.list()

# 1. Extract model names (safe for both object and dict responses)
all_models = [m.model for m in models_info.models] if hasattr(models_info, 'models') else [m['name'] for m in models_info.get('models', [])]

# 2. Filter out embeddings: remove any name containing "embed"
available_models = [m for m in all_models if "embed" not in m.lower()]

# 3. Set preferred model
PREFERRED_MODEL = "mistral"

# 4. Find preferred model (exact match or with :latest tag)
active_model = next(
    (m for m in available_models if m == PREFERRED_MODEL or m == f"{PREFERRED_MODEL}:latest"),
    None
)

# 5. Fallback if preferred model is not downloaded
if active_model is None:
    if available_models:
        active_model = available_models[0]
        print(f"⚠️ '{PREFERRED_MODEL}' not found. Using fallback: {active_model}")
    else:
        raise RuntimeError("❌ No LLM models downloaded in Ollama")

print("Available LLMs:", available_models)
print(f"✅ Active model: {active_model}")

# --- Reusable Function ---
def get_active_model(preferred: str = "mistral") -> str:
    all_models = [m.model for m in ollama.list().models]
    llms = [m for m in all_models if "embed" not in m.lower()]
    
    selected = next((m for m in llms if m == preferred or m == f"{preferred}:latest"), None)
    return selected or (llms[0] if llms else "")

print(get_active_model(preferred=PREFERRED_MODEL))