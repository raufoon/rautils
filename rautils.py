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
            
###############################
#--------------Ø--------------#
###############################
