from __future__ import annotations

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import yaml

CONFIG_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(__file__),
    ), 'config.yaml',
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
REPORT_PATH = os.path.join(OUTPUT_DIR, 'report.html')


class CameraStreamChecker:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.streams = self._load_streams()
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def _load_streams(self):
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        return config.get('go2rtc', {}).get('streams', {})

    def parse_stream_params(self, path):
        # Извлекает параметры из строки после #
        if '#' not in path:
            return {}
        params = {}
        after_hash = path.split('#', 1)[1]
        for part in after_hash.split('#'):
            for kv in part.split('&'):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    params[k] = v
                elif kv:
                    # параметры типа video=h264
                    if '=' in kv:
                        k, v = kv.split('=', 1)
                        params[k] = v
                    elif kv.count(':') == 1:
                        k, v = kv.split(':', 1)
                        params[k] = v
                    elif kv:
                        params[kv] = True
        return params

    def ffprobe_stream(self, url):
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-rtsp_transport', 'tcp', '-v', 'error', '-select_streams', 'v:0',
                    '-show_entries', 'stream=codec_name,width,height,avg_frame_rate',
                    '-of', 'default=noprint_wrappers=1', url,
                ], capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return {'error': result.stderr.strip() or 'ffprobe failed'}
            info = {}
            for line in result.stdout.splitlines():
                if '=' in line:
                    k, v = line.split('=', 1)
                    info[k.strip()] = v.strip()
            return info
        except Exception as e:
            return {'error': str(e)}

    def process_stream(self, stream_name, url):
        url_for_probe = url.split('#', 1)[0]
        probe_info = self.ffprobe_stream(url_for_probe)
        return (url, probe_info)

    def check_streams(self, max_workers=None):
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            max_workers = min(32, cpu_count * 2)
        print(f'STREAMS _raw CHECK (workers={max_workers}):')
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for stream_name, stream_urls in self.streams.items():
                if not stream_name.endswith('_raw'):
                    continue
                for url in stream_urls:
                    if url.startswith('rtsp://'):
                        future = executor.submit(
                            self.process_stream, stream_name, url,
                        )
                        futures.append((stream_name, future))
                    else:
                        if stream_name not in results:
                            results[stream_name] = []
                        results[stream_name].append((url, None))
            for stream_name, future in futures:
                if stream_name not in results:
                    results[stream_name] = []
                results[stream_name].append(future.result())
        self.generate_html_report(results)

    def generate_html_report(self, results):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html = [
            '<!DOCTYPE html>',
            '<html lang="ru"><head><meta charset="utf-8"><title>Camera Streams Report</title>',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<style>',
            'body { background: #181c20; color: #f3f3f3; font-family: "Segoe UI", Arial, sans-serif; margin: 0; padding: 0; }',
            'h1 { text-align: center; margin-top: 32px; font-size: 2.5em; letter-spacing: 2px; }',
            'h2 { margin-top: 40px; color: #7ecfff; border-bottom: 1px solid #333; padding-bottom: 8px; }',
            '.container { display: flex; flex-wrap: wrap; gap: 32px; justify-content: center; margin: 32px auto; max-width: 1600px; }',
            '.card { background: #23272e; border-radius: 18px; box-shadow: 0 4px 32px #000a, 0 1.5px 6px #0004; padding: 24px 20px 18px 20px; min-width: 320px; max-width: 340px; flex: 1 1 320px; margin-bottom: 24px; opacity: 0; transform: translateY(40px) scale(0.98); animation: fadeInUp 0.7s forwards; }',
            '.card:nth-child(1) { animation-delay: 0.1s; } .card:nth-child(2) { animation-delay: 0.2s; } .card:nth-child(3) { animation-delay: 0.3s; } .card:nth-child(4) { animation-delay: 0.4s; } .card:nth-child(5) { animation-delay: 0.5s; }',
            '@keyframes fadeInUp { to { opacity: 1; transform: translateY(0) scale(1); } }',
            '.ok { color: #7fff7e; font-weight: bold; }',
            '.fail { color: #ff7e7e; font-weight: bold; }',
            '.meta { font-size: 1.05em; margin-bottom: 6px; }',
            '.url { font-size: 0.95em; color: #7ecfff; word-break: break-all; margin-bottom: 8px; }',
            '.section-title { margin: 48px 0 16px 0; font-size: 1.5em; color: #7ecfff; letter-spacing: 1px; }',
            '</style>',
            '</head><body>',
            '<h1>Camera Streams Report</h1>',
            f'<p style="text-align:center; color:#aaa;">Generated: {now}</p>',
        ]
        for stream_name, items in results.items():
            html.append(f'<div class="section-title">{stream_name}</div>')
            html.append('<div class="container">')
            for idx, (url, future_probe) in enumerate(items):
                params = self.parse_stream_params(url)
                codec = params.get('video', 'unknown')
                width = params.get('width', 'unknown')
                html.append(
                    f'<div class="card" style="animation-delay:{0.1+idx*0.07:.2f}s">',
                )
                html.append(
                    f'<div class="meta"><b>Config:</b> codec={codec}, width={width}</div>',
                )
                html.append(f'<div class="url">{url}</div>')
                probe_info = future_probe if future_probe else None
                if probe_info:
                    if 'error' in probe_info:
                        html.append(
                            f'<div class="fail">[FAIL] ffprobe: {probe_info["error"]}</div>',
                        )
                    else:
                        html.append('<div class="ok">[OK] ffprobe:</div>')
                        html.append('<div class="meta">')
                        html.append(
                            ', '.join([
                                f'codec={probe_info.get("codec_name", "?")}',
                                f'width={probe_info.get("width", "?")}',
                                f'height={probe_info.get("height", "?")}',
                                f'fps={probe_info.get("avg_frame_rate", "?")}',
                            ]),
                        )
                        html.append('</div>')
                html.append('</div>')
            html.append('</div>')
        html.append('</body></html>')
        with open(REPORT_PATH, 'w') as f:
            f.write('\n'.join(html))
        print(f'HTML report generated: {REPORT_PATH}')


if __name__ == '__main__':
    checker = CameraStreamChecker()
    checker.check_streams()
