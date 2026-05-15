# Instructions to Run

### 1.1. sync dependencies
uv sync

### 1.2. Activate environment
source .venv/scripts/activate

### 1.3. Install playwright
playwright install

### 1.3. Run Local App
uv run main.py

### 1.3. Run Local App
streamlit run app.py


### Ejecutar en power shell como administrador (si no no funciona)
choco install graphviz -y

### Ejecutar dentro del proyecto
    uv pip install pygraphviz \
    --config-settings="--global-option=build_ext" \
    --config-settings="--global-option=-I/c/Program Files/Graphviz/include" \
    --config-settings="--global-option=-L/c/Program Files/Graphviz/lib"