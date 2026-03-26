# TrendStage

Generate trending topic videos with CLI + Web App + OBS.

## Quick Start

### 1. Generate Assets
```bash
cd cli
pip install -r requirements.txt
python trendstage.py --topic "Chelsea VAR"
```

### 2. Open Web App
```
open ../webapp/index.html
```

### 3. Record with OBS
- Fullscreen the web app
- OBS → Record
- Press keys to switch views:
  - `1` Graph
  - `2` Clip
  - `3` Comments
  - `Q`/`E` Next/Prev graph state
  - `0` Reset

### 4. Trim & Post

## Output
Assets go to `webapp/assets/`:
- `config.json` - Stage layout
- `graph_0.png` - Graph full
- `graph_1.png` - Graph highlight
- `graph_2.png` - Graph zoom
- `graph_3.png` - Graph compare
- `clip_preview.png` - Clip preview
- `stats.json` - Stats data
- `comments.json` - Comments data

## Pundit Pipeline → Webapp Topics

Generate fresh topics and auto-populate the webapp:
```bash
export TRENDSTAGE_TOPICS_PATH="$(pwd)/webapp/topics"
cd pundit_pipeline/pipeline
python3 run_pipeline_v2.py
```

Serve the webapp locally (matches your `http://localhost:8888/index.html` setup):
```bash
cd ../../webapp
python3 -m http.server 8888
```

Topic images are cached to `webapp/assets/topic_images/` so they load reliably in the browser.
