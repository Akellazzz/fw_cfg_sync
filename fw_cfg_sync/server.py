# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
from main import load_inventory
from main import get_devices_by_function


hostName = "localhost"
serverPort = 443

page = '''
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
}

table.center {
  margin-left: auto; 
  margin-right: auto;
}
</style>
</head>
<body>
<table class="center">
<tr>
<th>Firstname</th>
<th>Lastname</th> 
<th>Age</th>
</tr>
<tr>
<td>Jill</td>
<td>Smith</td>
<td>50</td>
</tr>
<tr>
<td>Eve</td>
<td>Jackson</td>
<td>94</td>
</tr>
<tr>
<td>John</td>
<td>Doe</td>
<td>80</td>
</tr>
</table>

</body>
</html>

'''
def get_inventory():    
    inv = load_inventory(r'C:\Users\eekosyanenko\Documents\fw_cfg_sync\app_config\inventory\multicontext.yaml')

    firewalls = get_devices_by_function(inv, "fw")


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        for line in page.strip():
            self.wfile.write(line.encode('utf-8'))    

if __name__ == "__main__":   
    get_inventory()
      

    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")