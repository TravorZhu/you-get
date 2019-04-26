import json
import queue
import threading
import tkinter as tk
from queue import Queue
from tkinter import ttk

from you_get.common import *

_srcdir = '%s/src/' % os.path.dirname(os.path.realpath(__file__))
_filepath = os.path.dirname(sys.argv[0])
sys.path.insert(1, os.path.join(_filepath, _srcdir))


class main_window(tk.Tk):
    download_inf_queue = Queue()

    def __init__(self):
        super().__init__()

        self.path = tk.StringVar(self)

        self.path.set(_filepath)
        
        self.url_label = tk.Label(self, text='Url')
        self.url_input = tk.Entry(self, width=50)
        self.path_label = tk.Label(self, text='save path')
        self.path_input = tk.Entry(self, width=40, textvariable=self.path)
        self.path_button = tk.Button(self, text='...', command=self.select_path)
        
        self.start_btn = tk.Button(self, text='Start Download', command=self.start_download)
        
        self.url_label.grid(column=0, row=0)
        self.url_input.grid(column=1, row=0, columnspan=2)
        self.path_label.grid(column=0, row=1)
        self.path_input.grid(column=1, row=1)
        self.path_button.grid(column=2, row=1)
        self.start_btn.grid(column=0, row=2, columnspan=2)
        
        # self.progress_label_text = tk.StringVar()
        # self.speed_label_text = tk.StringVar()
        self.progressbar = ttk.Progressbar(self, maximum=100, length=200)
        self.progressbar.grid(column=0, row=3, columnspan=2)
        self.progressbar['value'] = 0
        self.progressbar.grid_forget()
        self.progresslabel = tk.Label(self)
        
        self.speedlabel = tk.Label(self)
        
        self.progressbar['value'] = 0
        self.is_start_download = False
        self.detail_things = []
        # self.speedlabel = '   0  B/s'

    def select_path(self):
        import tkinter.filedialog
    
        self.path.set(tkinter.filedialog.askdirectory())
    
    def show_detail(self):
        self.progressbar.grid(column=0, row=3, columnspan=3)
        self.progresslabel.grid(column=0, row=4)
        self.speedlabel.grid(column=1, row=4, columnspan=2)
        try:
            with open('tem.json', 'r') as f:
                data = json.loads(f.read())
                print(data)
            os.remove('tem.json')
            for i, (name, value) in enumerate(data.items()):
                label = tk.Label(self, text=name)
                entry = tk.Entry(self, width=40)
                entry.insert(tk.END, str(value))
                label.grid(column=0, row=5 + i)
                entry.grid(column=1, row=5 + i, columnspan=2)
                self.detail_things.append((label, entry))
        except Exception as e:
            print(e)
    
    def hide_detail(self):
        self.start_btn.config(state=tk.NORMAL)
        self.progresslabel.grid_forget()
        self.speedlabel.grid_forget()
        self.progressbar.grid_forget()
        for (e, l) in self.detail_things:
            e.grid_forget()
            l.grid_forget()
        self.detail_things = []
    
    def start_download(self):
        self.start_btn.config(state=tk.DISABLED)
        self.get_message_from_downloader()
        threading.Thread(target=self.start_download_thread).start()
    
    def start_download_thread(self):
        try:
            global download_inf_queue
            download_inf_queue = self.download_inf_queue
            extra = {}
            URLs = [self.url_input.get()]
            download_main(
                any_download, any_download_playlist,
                URLs, None, download_inf_queue, output_dir=self.path_input.get(),
                merge=not None,
                info_only=None, json_output=None, caption=None,
                password=None,
                **extra
            )
        finally:
            self.hide_detail()
    
    def get_message_from_downloader(self):
        try:
            result = self.download_inf_queue.get(False)
            # self.progress_label_text = int(result['progress'])
            # self.speed_label_text = result['speed']
            self.progresslabel.config(text='{}%'.format(int(result['progress'])))
            self.speedlabel.config(text=result['speed'])
            # print(result)
            self.progressbar['value'] = int(result['progress'])
            if not self.is_start_download:
                self.is_start_download = True
                self.show_detail()
            self.update()
            # self.progresslabel['text'] = '{}%'.format(progress)
            # self.speedlabel['text'] = speed
        except queue.Empty:
            pass
        finally:
            if self.progressbar['value'] < self.progressbar['maximum']:
                self.after(80, self.get_message_from_downloader)


def ui_main():
    main_window().mainloop()
    
if __name__ == '__main__':
    main_window().mainloop()
