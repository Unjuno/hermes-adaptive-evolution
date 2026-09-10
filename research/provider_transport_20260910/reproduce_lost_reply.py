"""Local reviewed HTTP counterexample; NOT Ollama/Hermes inference or billing."""
from __future__ import annotations
import argparse, hashlib, http.client, json, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def trial(attempts):
    state={'processed':0}
    class H(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            state['processed']+=1
            time.sleep(.12)  # operation recorded, reply later than client timeout
            raw=b'{"done":true,"response":"ok"}'
            self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers()
            try:self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),H);server.daemon_threads=True
    thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01});thread.start()
    errors=[];body=b'{"request":"same-reviewed-input"}'
    try:
        for _ in range(attempts):
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=.03)
            try:c.request('POST','/reviewed',body=body);c.getresponse().read()
            except (OSError,http.client.HTTPException) as e:errors.append(type(e).__name__)
            finally:c.close()
        return {'client_attempts':attempts,'server_processed':state['processed'],
                'client_errors':errors,'same_payload_sha256':hashlib.sha256(body).hexdigest()}
    finally:server.shutdown();thread.join();server.server_close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('refuse existing output')
    result={'schema':'hermes.lost-reply-reviewed-counterexample.v1',
            'no_retry':trial(1),'naive_retry_three':trial(3),
            'real_model':False,'real_money_measured':False,'execution_authorized':False,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':sys.version}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
