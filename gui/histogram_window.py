import tkinter as tk
from tkinter import ttk
import numpy as np
import cv2

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HistogramWindow(tk.Toplevel):
    def __init__(self, parent, orig_path, stego_path):
        super().__init__(parent)
        self.title("Histogram Comparison")
        self.geometry("900x550")

        self.orig_path = orig_path
        self.stego_path = stego_path
        self._orig_frames = []
        self._stego_frames = []

        self._load_frames()

        ctrl = ttk.Frame(self)
        ctrl.pack(fill='x', padx=8, pady=4)
        ttk.Label(ctrl, text="Frame:").pack(side='left')
        self.frame_var = tk.IntVar(value=0)
        n = max(len(self._orig_frames) - 1, 0)
        self.spin = ttk.Spinbox(ctrl, from_=0, to=n, textvariable=self.frame_var, width=6,
                                command=self._update_plot)
        self.spin.pack(side='left', padx=4)
        ttk.Button(ctrl, text="Refresh", command=self._update_plot).pack(side='left', padx=4)

        self.fig = Figure(figsize=(9, 4.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self._update_plot()

    def _load_frames(self):
        for path, store in [(self.orig_path, self._orig_frames),
                            (self.stego_path, self._stego_frames)]:
            cap = cv2.VideoCapture(path)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                store.append(frame)
            cap.release()

    def _update_plot(self):
        idx = self.frame_var.get()
        if idx >= len(self._orig_frames) or idx >= len(self._stego_frames):
            return

        orig = self._orig_frames[idx]
        stego = self._stego_frames[idx]

        self.fig.clear()
        colors = ['b', 'g', 'r']
        labels = ['Blue', 'Green', 'Red']

        for i, (color, label) in enumerate(zip(colors, labels)):
            ax = self.fig.add_subplot(1, 3, i + 1)
            ax.hist(orig[:, :, i].ravel(), bins=256, range=(0, 256),
                    alpha=0.5, color=color, label=f'Original')
            ax.hist(stego[:, :, i].ravel(), bins=256, range=(0, 256),
                    alpha=0.5, color='orange', label='Stego')
            ax.set_title(label)
            ax.legend(fontsize=7)
            ax.set_xlim(0, 256)

        self.fig.tight_layout()
        self.canvas.draw()
