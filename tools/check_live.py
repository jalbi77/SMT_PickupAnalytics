"""Lesender Praxistest; Ausgabe enthält nur aggregierte Prüfergebnisse."""
import json
import sys
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data import load_data
from analysis import calculate, SPECS

device, nozzle = load_data()
report = {'device_rows': len(device), 'nozzle_rows': len(nozzle),
          'exact_duplicate_device_rows': int(device.duplicated().sum()),
          'exact_duplicate_nozzle_rows': int(nozzle.duplicated().sum()), 'categories': {}}
for name in SPECS:
    frame, missing = calculate(nozzle if name == 'Saugdüsen' else device, name)
    report['categories'][name] = {'units': len(frame), 'missing_id_rows': missing,
                                'zero_denominator_units': int(frame.ErrorIndex.isna().sum())}
app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'main.py')).run(timeout=30)
with patch('data.load_data', return_value=(device, nozzle)):
    app.button[0].click().run(timeout=60)
if app.exception or app.error or len(app.dataframe) != 3:
    raise RuntimeError('Oberflächenprüfung mit echten Daten fehlgeschlagen')
report['live_ui'] = 'OK: drei Tabellen und Diagramme ohne App-Fehler'
Path('diagnostics').mkdir(exist_ok=True)
Path('diagnostics/live_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
