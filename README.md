# LLM_PT_Alerts

**LLM Demonstrator using GTFS-Realtime public transport service alerts.**

This repository accompanies the paper: *Large Language Models for Sustainable Transport: Addressing Language Bottlenecks to Advance Equity, Safety, and Low-Emission Mobility* (submitted to Journal of Cleaner Production, 2025).

The demonstrator processes GTFS-Realtime alerts (train, tram, and bus) and applies large language models (LLMs) to:
- Parse and normalise route identifiers
- Generate plain-language passenger summaries
- Translate alerts into Mandarin and Arabic
- Compute run-level metrics (alerts processed, mode counts, route resolution rate)

### Repository structure
- `scripts/` : Python scripts for preprocessing and summarisation  
- `config/` : Sample GTFS reference files and configuration templates  
- `data/` : Example input alerts and sample outputs (non-sensitive, anonymised)  
- `results/` : Tables and figures generated from demonstrator runs  
- `requirements.txt` : Python package dependencies  

### Usage
```bash
# Clone repository
git clone https://github.com/hdia/LLM_PT_Alerts.git
cd LLM_PT_Alerts

# Install dependencies
pip install -r requirements.txt

# Run summariser (example for Melbourne)
python scripts/summarise_runs.py "data/sample_alerts/out*_MEL.csv"

