import http.server
import socketserver
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

PORT = 8000
REPORT_FILE = "risk_report.html"

class ReportHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Disable caching to ensure latest report is shown
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        # Redirect root path to the report file
        if self.path == '/' or self.path == '/index.html':
            if os.path.exists(REPORT_FILE):
                self.path = REPORT_FILE
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Risk report not generated yet.</h1><p>Please wait for the monitor to run.</p>")
                return
        
        return super().do_GET()

if __name__ == "__main__":
    # Allow port to be set via environment variable
    port = int(os.environ.get("PORT", PORT))
    
    logging.info(f"Starting Report Server on port {port}...")
    logging.info(f"Access the report at http://localhost:{port}")
    
    with socketserver.TCPServer(("", port), ReportHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
