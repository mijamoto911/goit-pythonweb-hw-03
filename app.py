import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
from datetime import datetime
from jinja2 import Template


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(content_length)
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {
            key: value for key, value in [el.split("=") for el in data_parse.split("&")]
        }
        self.save_data(data_dict)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.render_page("index.html")
        elif pr_url.path == "/message":
            self.render_page("message.html")
        elif pr_url.path == "/read":
            self.render_read_page()
        elif pr_url.path.startswith("/static/"):
            self.send_static()
        else:
            self.render_page("error.html", status=404)

    def send_static(self):
        file_path = pathlib.Path("static") / self.path[8:]
        print(f"Requested path: {self.path}")
        print(f"Resolved file path: {file_path}")
        if not file_path.exists():
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")
            print(f"File not found: {file_path}")
            return

        self.send_response(200)
        mt = mimetypes.guess_type(str(file_path))
        if mt[0]:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "application/octet-stream")
        self.end_headers()
        with open(file_path, "rb") as file:
            self.wfile.write(file.read())

    def save_data(self, data):
        storage_path = pathlib.Path("storage/data.json")
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not storage_path.exists():
            storage_path.write_text("{}")

        with open(storage_path, "r+") as file:
            current_data = json.load(file)
            timestamp = datetime.now().isoformat()
            current_data[timestamp] = data
            file.seek(0)
            json.dump(current_data, file, indent=4)

    def render_page(self, template_name, context={}, status=200):
        file_path = pathlib.Path("templates") / template_name
        if not file_path.exists():
            self.render_page("error.html", status=404)
            return

        with open(file_path, "r") as template_file:
            html_template = template_file.read()

        template = Template(html_template)
        rendered_html = template.render(context)

        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_html.encode())

    def render_read_page(self):
        storage_path = pathlib.Path("storage/data.json")
        if not storage_path.exists():
            self.render_page("error.html", status=404)
            return

        with open(storage_path, "r") as file:
            messages = json.load(file)

        file_path = pathlib.Path("templates/read.html")
        if not file_path.exists():
            self.render_page("error.html", status=404)
            return

        with open(file_path, "r") as template_file:
            html_template = template_file.read()

        template = Template(html_template)
        rendered_html = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_html.encode())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        print("Starting server on port 3000...")
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        http.server_close()


if __name__ == "__main__":
    run()
