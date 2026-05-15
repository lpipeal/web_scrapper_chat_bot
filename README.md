# Instructions to Run

### 1.1. sync dependencies
uv sync

### 1.2. Activate environment
source .venv/scripts/activate

### 1.3. Install playwright
playwright install

### 1.4. Install playwright
Modificar
.env.example

Dejarlo y poner sus credenciales
.env

### 1.5. Run Local Batch App
uv run run_batch.py

### 1.6. Run Local App
streamlit run  run_app.py

### 1.7. Run Test Local App
uv run test_rag.py

## No necesario instalarlo por ahora
### Ejecutar en power shell como administrador (si no no funciona)
choco install graphviz -y

### Ejecutar dentro del proyecto
    uv pip install pygraphviz \
    --config-settings="--global-option=build_ext" \
    --config-settings="--global-option=-I/c/Program Files/Graphviz/include" \
    --config-settings="--global-option=-L/c/Program Files/Graphviz/lib"