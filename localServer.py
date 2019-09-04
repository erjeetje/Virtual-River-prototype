# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 11:30:47 2019

@author: HaanRJ
"""

import os
import http.server
import socketserver


def run_server(web_path, path=os.path.dirname(__file__)):
    """
    try:
        os.mkdir(web_path)
        print("Directory ", web_path, " Created.")
    except FileExistsError:
        print("Directory ", web_path,
              " already exists, overwriting files.")
    """
    os.chdir(web_path)
    
    PORT = 8000
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
    os.chdir(path)
    return


def main():
    path=os.path.dirname(__file__)
    web_path = os.path.join(path, 'webserver')
    run_server(web_path, path=path)
    return
    
    
if __name__ == '__main__':
    main()
