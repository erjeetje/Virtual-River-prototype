# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 11:30:47 2019

@author: HaanRJ
"""

import os
import http.server
import socketserver
import _thread as thread


class Webserver():
    def __init__(self):
        self.path = None
        self.web_path = None
        self.setup()
        thread.start_new_thread(self.run_server, ())
        return
        
    def setup(self):
        self.path = os.path.dirname(__file__)
        self.web_path = os.path.join(self.path, 'webserver')
        return
    
    
    def run_server(self):
        """
        try:
            os.mkdir(web_path)
            print("Directory ", web_path, " Created.")
        except FileExistsError:
            print("Directory ", web_path,
                  " already exists, overwriting files.")
        """
        os.chdir(self.web_path)
        
        PORT = 8000
        
        Handler = http.server.SimpleHTTPRequestHandler
        
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("serving at port", PORT)
            httpd.serve_forever()
        #os.chdir(self.path)
        return


def main():
    
    server = Webserver()
    #run_server(web_path, path=path)
    return
    
    
if __name__ == '__main__':
    main()
