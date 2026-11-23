"""Tkinter front end for the Beam Designer."""

import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from beam_calculations import UniformLoad, analyze
from member_data import MEMBERS


class BeamApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Beam Designer")
        self.geometry("1120x760")
        self.minsize(780, 600)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.vars = {}
        self.errors = {}
        self._build()
        self.calculate()

    def _build(self):
        left = ttk.Frame(self, padding=14)
        left.grid(row=0, column=0, sticky="nsw")
        right = ttk.Frame(self, padding=14)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        ttk.Label(left, text="Beam Designer", font=("TkDefaultFont", 16, "bold")).grid(sticky="w", pady=(0, 12))
        self._combo(left, "Support", ("Simply supported", "Cantilever"), "Simply supported")
        self._entry(left, "Span (ft)", "20")
        self._combo(left, "Member", tuple(MEMBERS), tuple(MEMBERS)[0])
        self._entry(left, "Additional safety factor", "1.0")
        ttk.Separator(left).grid(sticky="ew", pady=10)
        ttk.Label(left, text="Uniform load · kip/ft").grid(sticky="w")
        self._entry(left, "Intensity", "1.0")
        self._entry(left, "Start (ft)", "0")
        self._entry(left, "End (ft)", "20")
        ttk.Button(left, text="Calculate", command=self.calculate).grid(sticky="ew", pady=10)
        self.status = ttk.Label(left, text="", wraplength=250)
        self.status.grid(sticky="w")
        self.results = ttk.Label(left, text="", justify="left", wraplength=250)
        self.results.grid(sticky="w", pady=10)
        for var in self.vars.values():
            var.trace_add("write", self._mark_stale)

        self.beam_label = ttk.Label(right, text="Beam and loading", font=("TkDefaultFont", 13, "bold"))
        self.beam_label.grid(row=0, column=0, sticky="w")
        self.figure = Figure(figsize=(7, 5), dpi=100, layout="constrained")
        self.axes = [self.figure.add_subplot(4, 1, i+1) for i in range(4)]
        self.canvas = FigureCanvasTkAgg(self.figure, master=right)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    def _entry(self, parent, label, value):
        ttk.Label(parent, text=label).grid(sticky="w", pady=(6, 0))
        var = tk.StringVar(value=value)
        ent = ttk.Entry(parent, textvariable=var, width=25)
        ent.grid(sticky="ew")
        self.vars[label] = var
        self.errors[label] = ent

    def _combo(self, parent, label, values, initial):
        ttk.Label(parent, text=label).grid(sticky="w", pady=(6, 0))
        var = tk.StringVar(value=initial)
        box = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=23)
        box.grid(sticky="ew")
        self.vars[label] = var
        self.errors[label] = box

    def _mark_stale(self, *_):
        if hasattr(self, "status"):
            self.status.configure(text="Inputs changed; press Calculate to update results.", foreground="#8a4b08")

    def calculate(self):
        try:
            span = float(self.vars["Span (ft)"].get())
            safety = float(self.vars["Additional safety factor"].get())
            intensity = float(self.vars["Intensity"].get())
            start = float(self.vars["Start (ft)"].get())
            end = float(self.vars["End (ft)"].get())
            values = (span, safety, intensity, start, end)
            if not all(np.isfinite(values)):
                raise ValueError("Enter finite numeric values in every field.")
            result = analyze(span, self.vars["Support"].get(), [UniformLoad(intensity, start, end)], MEMBERS[self.vars["Member"].get()], safety)
        except (ValueError, KeyError) as exc:
            self.status.configure(text=str(exc), foreground="#b42318")
            for ent in self.errors.values():
                ent.configure(style="Invalid.TEntry")
            self.style = ttk.Style(self)
            self.style.configure("Invalid.TEntry", fieldbackground="#ffd9d9")
            return
        for ent in self.errors.values():
            ent.configure(style="TEntry")
        self.status.configure(text="Results updated.", foreground="#18704e")
        self.results.configure(text=(f"Left reaction: {result['reaction_left_kip']:.3f} kip\n"
            f"Right reaction: {result['reaction_right_kip']:.3f} kip\n"
            f"Max |M|: {result['max_moment_kip_ft']:.3f} kip-ft\n"
            f"Bending: {result['bending_stress_ksi']:.3f} / {result['bending_limit_ksi']:.3f} ksi — {'PASS' if result['bending_pass'] else 'FAIL'}\n"
            f"Max |deflection|: {result['max_deflection_in']:.3f} / {result['deflection_limit_in']:.3f} in — {'PASS' if result['deflection_pass'] else 'FAIL'}"))
        self._plot(result, span, intensity, start, end, self.vars["Support"].get())

    def _plot(self, r, span, intensity, start, end, support):
        for ax in self.axes:
            ax.clear()
        x = r["x_ft"]
        ax = self.axes[0]
        ax.plot([0, span], [0, 0], color="#263b4a", lw=5)
        n = max(4, int(span*1.5))
        for px in np.linspace(start, end, n):
            ax.annotate("", (px, 0.18), (px, 0.55), arrowprops={"arrowstyle":"->", "color":"#b04c37"})
        ax.text(span/2, .65, f"{intensity:g} kip/ft", ha="center")
        if support == "Simply supported":
            ax.scatter([0, span], [-.12, -.12], marker="^", color="#176b87")
        else:
            ax.plot([0, 0], [-.35, .35], color="#176b87", lw=4)
        ax.set_xlim(-span*.03, span*1.03); ax.set_ylim(-.5, .9); ax.axis("off"); ax.set_title("Beam and loading")
        for ax, y, title, color in zip(self.axes[1:], (r["shear_kip"], r["moment_kip_ft"], r["deflection_in"]), ("Shear (kip)", "Moment (kip-ft)", "Deflection (in)"), ("#176b87", "#b04c37", "#18704e")):
            ax.plot(x, y, color=color); ax.axhline(0, color="#82919d", lw=.7); ax.set_ylabel(title); ax.grid(alpha=.2)
        self.axes[-1].set_xlabel("Position along span (ft)")
        self.canvas.draw_idle()


if __name__ == "__main__":
    BeamApp().mainloop()
