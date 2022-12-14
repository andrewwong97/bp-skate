import datetime
import json
from http.server import BaseHTTPRequestHandler

import requests


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.validate()

        # We need an extra boolean because BaseHTTPRequestHandler does not support early exits
        start_date = self.headers.get('startDate')
        print(f'Received {start_date} header param')
        uri = f"https://xola.com/api/experiences/61536b244f19be5b3c6e4241/availability?" \
              f"start={start_date}&end={start_date}&privacy=public"
        print(f'Making request to {uri}')
        r = requests.get(uri)
        print('Response ' + json.dumps(r.json()))
        available_times = self.get_available_times(r.json()[start_date])
        print('available_times=' + str(available_times))
        formatted_times = self.formatted_times(available_times)
        print('formatted_times=' + formatted_times)

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(formatted_times.encode('utf-8'))

    def validate(self):
        # Validate uri path
        if self.path != '/api':
            self.send_response(404, f'{self.path} not found')
            self.end_headers()
            return

        # Validate sender
        print(f"src={self.headers.get('src')}")
        if self.headers.get('src') != 'a':
            self.send_response(403, 'Forbidden: improper issuer')
            self.end_headers()
            return

    def get_available_times(self, times_dict):
        print('Times dict: ' + str(times_dict))
        return {t: v for t, v in times_dict.items() if v > 0}

    def formatted_times(self, times):
        formatted = []  # we use a list for performance benefit
        for t, v in times.items():
            formatted.append(f"{datetime.datetime.strptime(t, '%H%M').strftime('%I:%M %p')} has {v} slots open")
        return '\n'.join(formatted)
