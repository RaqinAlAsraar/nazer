import os
import re
import json
import csv
import sys
import asyncio
import argparse
import subprocess
import ssl
import urllib.request
import base64
from urllib.parse import urljoin, urlparse
from datetime import datetime

try:
    from mitmproxy import http
    from mitmproxy.options import Options
    from mitmproxy.tools.dump import DumpMaster
    from rich.console import Console
except ImportError:
    print("Dependencies missing. Please run: pip install mitmproxy rich")
    sys.exit(1)

class NazerProxy:
    def __init__(self, config, target_domain):
        self.config = config
        self.target_domain = target_domain.lower() if target_domain else None
        self.counter = 0
        self.seen_requests = set()
        self.console = Console()
        
        self.crawl_queue = asyncio.Queue()
        self.crawled_urls = set()
        if self.config.get("active_crawler"):
            asyncio.create_task(self.crawler_worker())
        
        if not os.path.exists(self.config["log_directory"]):
            os.makedirs(self.config["log_directory"])

        base_name = "nazer_log"
        if self.target_domain:
            base_name = self.target_domain.replace(".", "_")
            
        timestamp_str = ""
        if self.config["timestamp_in_filename"]:
            timestamp_str = f"_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}"

        ext_config = self.config.get("auto_extension", "html")
        self.formats = [ext.strip().lower() for ext in ext_config.split(",")]
        
        self.filepaths = {}
        for ext in self.formats:
            file_ext = "jsonl" if ext == "json" else ext
            filename = f"{base_name}{timestamp_str}.{file_ext}"
            self.filepaths[ext] = os.path.join(self.config["log_directory"], filename)
            
        self.init_output_file()
        
        self.console.print(f"[bold green][*] Nazer by @RaqinAlAsraar started on port {self.config['port']}[/bold green]")
        if self.config.get("active_crawler"):
            self.console.print("[bold cyan][*] Active Crawler (Spider) is ENABLED[/bold cyan]")
        if self.config.get("log_full_requests"):
            self.console.print("[bold yellow][*] Header Logging is ENABLED (HTML only)[/bold yellow]")
        for ext, path in self.filepaths.items():
            self.console.print(f"[*] Logging ({ext.upper()}): {path}")

    async def crawler_worker(self):
        while True:
            url = await self.crawl_queue.get()
            try:
                proxy_url = f"http://127.0.0.1:{self.config['port']}"
                proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ctx))
                opener.addheaders = [('User-Agent', 'Nazer-Active-Crawler/2.0')]
                await asyncio.to_thread(opener.open, url, timeout=5)
            except Exception:
                pass 
            finally:
                self.crawl_queue.task_done()

    def get_initiator(self, flow: http.HTTPFlow, is_crawler: bool):
        if is_crawler: return "Spider"
        fetch_mode = flow.request.headers.get("sec-fetch-mode", "")
        fetch_site = flow.request.headers.get("sec-fetch-site", "")
        if fetch_mode == "navigate" and fetch_site == "none": return "User (Typed)"
        elif fetch_mode == "navigate": return "User (Clicked)"
        elif fetch_mode in ["cors", "no-cors", "websocket"] or "image" in flow.request.headers.get("Accept", ""): return "Website (Auto)"
        else: return "Website (Auto)"

    def init_output_file(self):
        for ext, filepath in self.filepaths.items():
            if ext == "csv":
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["#", "Initiator", "Host", "Method", "URL", "Param", "Status", "Length", "MIME", "Timestamp"])
            elif ext == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    pass 
            elif ext == "html":
                html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Nazer Proxy Logs</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f0f2f5; }
        .header { background: #1a1a1a; color: #00ffcc; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; }
        table.dataTable { background: white; border-radius: 8px; font-weight: 500; font-size: 14px; }
        table.dataTable tbody td { padding: 8px 10px; }
        a.req-url { color: #0056b3; text-decoration: none; font-weight: bold; }
        a.req-url:hover { text-decoration: underline; color: #ff0055; }
        .status-ok { color: #28a745; font-weight: bold;}
        .status-err { color: #dc3545; font-weight: bold;}
        .init-user { color: #0056b3; font-weight: bold; }
        .init-site { color: #6c757d; }
        .init-spider { color: #ff0055; font-weight: bold; }
        td.details-control { background: url('https://datatables.net/examples/resources/details_open.png') no-repeat center center; cursor: pointer; width: 30px;}
        tr.shown td.details-control { background: url('https://datatables.net/examples/resources/details_close.png') no-repeat center center; }
        .req-details-box { background: #111111; color: #ffffff; padding: 18px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; word-wrap: break-word; font-size: 14.5px; font-weight: bold; max-height: 500px; overflow-y: auto; border-left: 5px solid #00ffcc; letter-spacing: 0.5px; }
        tfoot input { width: 100%; padding: 3px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0;">🛡️ Nazer Proxy Logs <span style="font-size: 0.6em; color: #ccc;">by <a href="https://github.com/RaqinAlAsraar" target="_blank" style="color: #00ffcc; text-decoration: none;">@RaqinAlAsraar</a></span></h2>
    </div>
    <table id="logsTable" class="display" style="width:100%">
        <thead>
            <tr>
                <th></th><th>#</th><th>Initiator</th><th>Host</th><th>Method</th><th>URL</th><th>Param</th><th>Status Code</th><th>Length</th><th>MIME Type</th><th>Timestamp</th>
            </tr>
        </thead>
        <tbody id="logBody">
            <!-- ROWS_END -->
        </tbody>
        <tfoot>
            <tr>
                <th></th><th>#</th><th>Init</th><th>Host</th><th>Method</th><th>URL</th><th>Param</th><th>Status</th><th>Length</th><th>MIME</th><th>Time</th>
            </tr>
        </tfoot>
    </table>
    <script>
        function formatDetails(base64Data) {
            if(!base64Data) return "<div class='req-details-box'>Header logging was disabled for this request.</div>";
            try {
                const decoded = decodeURIComponent(escape(window.atob(base64Data)));
                return "<div class='req-details-box'>" + decoded.replace(/</g, '&lt;').replace(/>/g, '&gt;') + "</div>";
            } catch(e) { return "Error decoding data."; }
        }

        $(document).ready(function() {
            $('#logsTable tfoot th').each(function () {
                var title = $(this).text();
                if(title) { $(this).html('<input type="text" placeholder="Filter ' + title + '" />'); }
            });

            var table = $('#logsTable').DataTable({ 
                "order": [[ 1, "desc" ]],
                "lengthMenu": [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                "pageLength": 25
            });

            table.columns().every(function () {
                var that = this;
                $('input', this.footer()).on('keyup change clear', function () {
                    if (that.search() !== this.value) { that.search(this.value).draw(); }
                });
            });

            $('#logsTable tbody').on('click', 'td.details-control', function () {
                var tr = $(this).closest('tr');
                var row = table.row(tr);
                if (row.child.isShown()) {
                    row.child.hide();
                    tr.removeClass('shown');
                } else {
                    row.child(formatDetails(tr.attr('data-full-req'))).show();
                    tr.addClass('shown');
                }
            });
        });
    </script>
</body>
</html>"""
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_template)

    def write_log(self, data):
        for ext, filepath in self.filepaths.items():
            if ext == "csv":
                with open(filepath, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([data['index'], data['initiator'], data['host'], data['method'], data['url'], data['param'], data['status'], data['length'], data['mime'], data['timestamp']])
            elif ext == "json":
                json_data = data.copy()
                json_data.pop("full_data", None) 
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(json_data) + "\n")
            elif ext == "html":
                status_class = "status-ok" if data['status'] < 400 else "status-err"
                init = data['initiator']
                init_class = "init-spider" if "Spider" in init else ("init-user" if "User" in init else "init-site")
                
                display_url = data['url']
                if len(display_url) > 100: display_url = display_url[:97] + "..."
                url_link = f"<a class='req-url' href='{data['url']}' title='{data['url']}' target='_blank' style='word-wrap: break-word; display: inline-block; max-width: 400px;'>{display_url}</a>"
                
                full_req_b64 = ""
                if self.config.get("log_full_requests") and data.get('full_data'):
                    full_req_b64 = base64.b64encode(data['full_data'].encode('utf-8', errors='ignore')).decode('utf-8')

                row = f"<tr data-full-req='{full_req_b64}'><td class='details-control'></td><td>{data['index']}</td><td class='{init_class}'>{init}</td><td>{data['host']}</td><td>{data['method']}</td>"
                row += f"<td>{url_link}</td>"
                row += f"<td>{data['param']}</td><td class='{status_class}'>{data['status']}</td><td>{data['length']}</td>"
                row += f"<td>{data['mime']}</td><td>{data['timestamp']}</td></tr>\n            <!-- ROWS_END -->"
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = content.replace("<!-- ROWS_END -->", row)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

    def response(self, flow: http.HTTPFlow):
        if flow.request.url.startswith("data:"): return
            
        host = flow.request.host
        if host in ["127.0.0.1", "localhost"] and flow.request.port == self.config["port"]: return
        if self.target_domain and self.target_domain not in host.lower(): return

        method = flow.request.method
        url = flow.request.url
        clean_url_no_fragments = url.split('#')[0]
        self.crawled_urls.add(clean_url_no_fragments)

        if self.config["deduplicate"]:
            req_hash = f"{method}|{url}"
            if req_hash in self.seen_requests: return
            self.seen_requests.add(req_hash)

        is_crawler = flow.request.headers.get("User-Agent", "").startswith("Nazer-Active-Crawler")
        initiator = self.get_initiator(flow, is_crawler)
        has_params = "Yes" if (len(flow.request.query) > 0 or (method == "POST" and len(flow.request.content) > 0)) else "No"
        
        self.counter += 1
        status_code = flow.response.status_code
        length = len(flow.response.content) if flow.response.content else 0
        mime_type = flow.response.headers.get("Content-Type", "unknown").split(';')[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = {
            "index": self.counter,
            "initiator": initiator,
            "host": host,
            "method": method,
            "url": url,
            "param": has_params,
            "status": status_code,
            "length": length,
            "mime": mime_type,
            "timestamp": timestamp
        }

        if self.config.get("log_full_requests"):
            req_headers = "\n".join([f"{k}: {v}" for k, v in flow.request.headers.items()])
            res_headers = "\n".join([f"{k}: {v}" for k, v in flow.response.headers.items()])
            
            full_data = f"========== REQUEST HEADERS ==========\n{method} {flow.request.path} {flow.request.http_version}\n{req_headers}\n\n"
            full_data += f"========== RESPONSE HEADERS ==========\nHTTP {status_code}\n{res_headers}"
            log_entry["full_data"] = full_data

        self.write_log(log_entry)

        if self.config.get("active_crawler") and status_code == 200:
            content = flow.response.get_text(strict=False)
            if content and any(x in mime_type for x in ["html", "javascript", "json"]):
                attr_links = re.findall(r'(?:href|src|action|data-url)=[\'"]?([^\'" >]+)', content)
                raw_urls = re.findall(r'https?://[a-zA-Z0-9./?=_-]+', content)
                api_paths = re.findall(r'[\'"](/api/[^\'"]+)[\'"]', content, re.IGNORECASE)
                all_extracted = set(attr_links + raw_urls + api_paths)
                
                for link in all_extracted:
                    full_url = urljoin(url, link)
                    parsed_url = urlparse(full_url)
                    if parsed_url.scheme in ['http', 'https']:
                        if not self.target_domain or self.target_domain in parsed_url.netloc.lower():
                            clean_target = full_url.split('#')[0]
                            if clean_target not in self.crawled_urls and not clean_target.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.woff', '.woff2')):
                                self.crawled_urls.add(clean_target)
                                self.crawl_queue.put_nowait(clean_target)

        if is_crawler:
            self.console.print(f"[cyan]{self.counter} | 🕷️  SPIDER | {host} | Status: {status_code}[/cyan]")
        else:
            color = "green" if status_code < 400 else "red"
            init_display = "👤" if "User" in initiator else "🌐"
            self.console.print(f"[{color}]{self.counter} | {init_display} {method} | {host} | Status: {status_code}[/{color}]")

def load_config():
    nazer_dir = os.path.expanduser("~/.nazer")
    config_path = os.path.join(nazer_dir, "config.json")
    
    if not os.path.exists(nazer_dir):
        os.makedirs(nazer_dir)
    
    if not os.path.exists(config_path):
        print(f"\n[*] Global config not found. Generating default at: {config_path}")
        default_config = """{
    "# PORT": "The port number Nazer will listen on",
    "port": 8080,

    "# AUTO_EXTENSION": "Comma-separated options: html, json, csv",
    "auto_extension": "html, csv, json",

    "# AUTO_LAUNCH_BROWSER": "true/false - Will open a sandboxed browser",
    "auto_launch_browser": true,

    "# LOG_DIRECTORY": "Path where logs will be saved (relative to where you run nazer)",
    "log_directory": "./nazer_logs",

    "# DEDUPLICATE": "true/false - If true, ignores identical requests",
    "deduplicate": true,

    "# TIMESTAMP_IN_FILENAME": "true/false - Appends date and time to filename",
    "timestamp_in_filename": true,

    "# ACTIVE_CRAWLER": "true/false - Silently extracts and visits links",
    "active_crawler": true,

    "# LOG_FULL_REQUESTS": "true/false - Logs HTTP headers only (HTML only)",
    "log_full_requests": true
}"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(default_config)
    else:
        print(f"\n[*] Loaded configuration from: {config_path}")
            
    try:
        with open(config_path, "r", encoding='utf-8') as f:
            cleaned_content = re.sub(r'^\s*#.*$', '', f.read(), flags=re.MULTILINE)
            return json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        print(f"[-] Error: '{config_path}' contains invalid JSON format.\nDetails: {e}")
        sys.exit(1)

def launch_browser(port, target_domain):
    print(f"[*] Auto-launching browser configured for proxy 127.0.0.1:{port}...")
    chrome_paths = ["google-chrome", "chrome", "chromium", "chromium-browser", r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    args = [f"--proxy-server=http://127.0.0.1:{port}", "--ignore-certificate-errors", "--ignore-certificate-errors-spki-list", "--test-type", "--user-data-dir=/tmp/nazer_profile"]
    
    if target_domain:
        args.append(target_domain if target_domain.startswith("http") else f"http://{target_domain}")

    for path in chrome_paths:
        try:
            subprocess.Popen([path] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except FileNotFoundError:
            continue
    print("[-] Could not find Chrome/Chromium to launch automatically.")

async def start_proxy(config, target_domain):
    opts = Options(listen_host='127.0.0.1', listen_port=config["port"], ssl_insecure=True)
    master = DumpMaster(opts, with_termlog=False, with_dumper=False)
    master.addons.add(NazerProxy(config, target_domain))
    
    if config.get("auto_launch_browser"):
        launch_browser(config["port"], target_domain)

    try: 
        await master.run()
    except KeyboardInterrupt: 
        master.shutdown()

def main():
    config = load_config()
    parser = argparse.ArgumentParser(description="Nazer - HTTP Proxy Logger & Crawler by @RaqinAlAsraar")
    parser.add_argument("-d", "--domain", help="Target domain to filter (e.g., example.com)", default="")
    parser.add_argument("-f", "--format", help="Override config format (e.g., html,csv)")
    args = parser.parse_args()

    target_domain = args.domain
    if len(sys.argv) == 1:
        try:
            target_domain = input("Site name/Domain to target (leave blank for all): ").strip()
            fmt_override = input(f"Output format (e.g., html,csv) [default: {config['auto_extension']}]: ").strip()
            if fmt_override: config["auto_extension"] = fmt_override
        except KeyboardInterrupt:
            print("\n[*] Setup cancelled by user. Exiting...")
            sys.exit(0)
            
    if args.format: config["auto_extension"] = args.format

    print("\n" + "="*50)
    print("🛡️  Starting Nazer Proxy & Spider".center(50))
    print(f"👨‍💻 Developer: @RaqinAlAsraar".center(50))
    print("="*50 + "\n")
    
    try:
        asyncio.run(start_proxy(config, target_domain))
    except KeyboardInterrupt:
        print("\n\n[!] CTRL+C detected. Shutting down Nazer gracefully...")
        print("[*] All logs have been saved securely.")
        sys.exit(0)

if __name__ == "__main__":
    main()
