"""Compatibility entry: final WMS/no-event-locator Fig. 1 only.
Historical candidate code remains at the pre-alignment Git commit.
"""
from pathlib import Path
import runpy
if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('render_fig1_final.py')), run_name='__main__')
