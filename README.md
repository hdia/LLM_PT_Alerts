# LLM_PT_Alerts

**LLM Demonstrator using GTFS-Realtime public transport service alerts.**

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

## Installation
Clone the repository and install the Python dependencies:
```bash
git clone https://github.com/hdia/LLM_PT_Alerts.git
cd LLM_PT_Alerts
pip install -r requirements.txt


### Quickstart (samples)
```bash
# Generate samples (already committed, but reproducible)
python scripts/make_samples.py --glob "data/full/MEL/alerts_*.csv" --city MEL --rows 80 --count 2
python scripts/make_samples.py --glob "data/full/SEQ/alerts_*.csv" --city SEQ --rows 80 --count 2
python scripts/make_samples.py --glob "data/full/SYD/alerts_*.csv" --city SYD --rows 80 --count 2

# Run summarisers (examples)
python scripts/summarise_runs.py "data/sample_alerts/mel_*.csv"
python scripts/summarise_runs.py "data/sample_alerts/seq_*.csv"
python scripts/summarise_runs_syd.py "data/sample_alerts/syd_*.csv"

# Validate outputs
python scripts/validate_outputs.py results/tables/_runs_summary_MEL.csv results/tables/_runs_summary_SYD.csv results/tables/_runs_summary_SEQ.csv

# Compute cross-city averages
python scripts/compute_averages.py --settings config/settings.yaml


### Usage
```bash
# Clone repository
git clone https://github.com/hdia/LLM_PT_Alerts.git
cd LLM_PT_Alerts

# Install dependencies
pip install -r requirements.txt

# Run summariser (example for Melbourne)
python scripts/summarise_runs.py "data/sample_alerts/out*_MEL.csv"

### Acknowledgements
This work was developed as part of research on LLM-assisted multilingual disruption alerts in public transport.  

