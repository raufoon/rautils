###############################
########## ipy-input ##########
###############################

import ipywidgets as ipy
def ipyinput(*widgets):
    import jupyter_ui_poll as poll, time; from IPython.display import display
    widgets = list(widgets)
    for i, widget in enumerate(widgets):
      if isinstance(widget, ipy.Button): continue
      if isinstance(widget, str): widget = ipy.Text(description = widget)
      if isinstance(widget, ipy.RadioButtons):
        widget.options = [(str(x),x) for x in widget.options] if not isinstance(widget.options[0], str) else widget.options
      widgets[i] = widget

    button = ipy.Button(description = "Submit")
    button_clicked = False
    def on_button_clicked(b):
        nonlocal button_clicked
        button_clicked,b.description,b.disabled = True,"Submitted",True
        for widget in widgets:
          widget.disabled = True
          if isinstance(widget, ipy.RadioButtons):
            original_value = widget.value
            for i in range(len(options:=list(widget.options))):
              if options[i][1] == widget.value: options[i] = (f'»{options[i][0]}«',options[i][1]); break
            widget.options, widget.value = options, original_value
    button.on_click(on_button_clicked)

    display(*widgets, button)
    with poll.ui_events() as poll_event:
        while not button_clicked: poll_event(10); time.sleep(0.5)
        
    return [widget.value for widget in widgets]

#--------------Ø--------------#

###############################
######## Download URLS ########
###############################

import requests
import urllib.parse
from lxml import html

def get_download_urls(file_name, keywords=[], skip_keywords=[], search_url = "https://www.google.com/search?q=%s"):
  ext = '.'+file_name.split('.')[-1]
  if 'google' in search_url:
    search_url = search_url % urllib.parse.quote(file_name)
  headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
  try:
    response = requests.get(search_url, headers=headers, timeout=2)
    response.raise_for_status()
    # Parse the response content with lxml
    tree = html.fromstring(response.content)
    # Use XPath to find all anchor tags with href attributes
    all_a = tree.xpath('//a[@href]')
  except:
    return set()

  results = set()
  for a_tag in all_a:
    dirurl=False
    href = a_tag.get('href', '').replace('%25','%')
    if any(keyword in href for keyword in skip_keywords): continue
    has_keywords = True if not keywords else False
    if 'url=' in href:
      href = href.split('url=')[-1]
    if href.startswith(search_url.split('dir=')[-1]):
      dirurl=True
      href = search_url.split('dir=')[0]+'dir='+href
    if 'dir=' in href:
      dirurl=True

    if ext in href and not href.endswith(ext): href = href.split(ext)[0]+ext
    if not has_keywords:  has_keywords = any(keyword in href.lower() for keyword in keywords)
    if "http" in href and 'google' not in href and ((file_name in href) or has_keywords):
        splithref = href.split('&ved=')
        result_url = splithref[0] if len(splithref) == 1 else urllib.parse.unquote(splithref[0])
        result_url = result_url.split('&h=')[0]
        urls=set()
        if 'google' in search_url and file_name not in result_url:
          urls.update(get_download_urls(file_name, keywords, skip_keywords,result_url))
        else:
          urls.add(result_url)
        for url in urls:
          if url.endswith(file_name):
            results.add(url)
  return results

#--------------Ø--------------#

###############################
######## Folder Server ########
###############################

import os
import threading
import http.server
import socketserver
import socket
import ctypes
import requests

class FolderServer:
    _server_thread = None
    _httpd = None
    _port = None
    _folder = None

    def __new__(cls, path=None):
        return cls._start_server(path)

    @classmethod
    def _start_server(cls, path=None):
        """Start the server and save the port number. Optionally set the directory path."""
        if cls._httpd is None or path != cls._folder:
            cls.stop(no_output=True)
            cls._port = cls._find_free_port()
            try:
                cls._folder = path or os.getcwd()

                Handler = http.server.SimpleHTTPRequestHandler
                cls._httpd = socketserver.TCPServer(
                    ("", cls._port),
                    lambda *args, **kwargs: Handler(*args, directory=cls._folder, **kwargs)
                )
                cls._server_thread = threading.Thread(target=cls._httpd.serve_forever)
                cls._server_thread.start()
                print(f"Server started on port {cls._port} serving directory {cls._folder}")
            except Exception as e:
                print(f"Failed to start server: {e}")
                cls._httpd = None
                cls._server_thread = None
                
        return cls

    @classmethod
    def _find_free_port(cls) -> int:
        """Find a free port to use for the server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    @classmethod
    def start(cls, path=None):
        """Start the server if not already running and return the port."""
        return cls(path)

    @classmethod
    def stop(cls, no_output=False):
        """Stop the server and shutdown the server thread if running."""
        if cls._httpd is not None:
            cls._httpd.shutdown()
            cls._server_thread.join()  # Wait for the server thread to exit
            cls._httpd.server_close()
            cls._httpd = None
            cls._server_thread = None

        # Forcefully terminate the thread if still alive
        if cls._server_thread and cls._server_thread.is_alive():
            tid = ctypes.c_long(cls._server_thread.ident)
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
                if not no_output:
                    print('Exception raise failure')
        if not no_output:
            print(f"Server on port {cls.port} stopped.")
        return cls

    @classmethod
    @property
    def port(cls) -> int:
        """Get the current port number, or None if the server is not running."""
        return cls._port

    @classmethod
    @property
    def url(cls) -> str:
        """Get the current url, or None if the server is not running."""
        return f"http://localhost:{cls._port}/"

    @classmethod
    @property
    def folder(cls) -> str:
        """Get the current serving folder."""
        return cls._folder
    
    @classmethod
    @property
    def fileslistHTML(cls, subfolder=""):
        """Get the list of files in the server folder as HTML."""
        response = requests.get(cls.url+subfolder)
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to access {server_url}, Status code: {response.status_code}"
            
#--------------Ø--------------#
