"""Tkinter front end for the Beam Designer."""

import json
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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
        self.results_current = False
        self.last_result = None
        self._build()
        self.calculate()

    def _design_data(self):
        span = float(self.vars["Span (ft)"].get())
        safety = float(self.vars["Additional safety factor"].get())
        intensity = float(self.vars["Intensity"].get())
        start = float(self.vars["Start (ft)"].get())
        end = float(self.vars["End (ft)"].get())
        support = self.vars["Support"].get()
        section = self.vars["Member"].get()
        # Analyze first so saves and opens obey the same limits and validation as Calculate.
        analyze(span, support, [UniformLoad(intensity, start, end)], MEMBERS[section], safety)
        return {
            "format": "beam-designer",
            "version": 1,
            "support": support,
            "span_ft": span,
            "section": section,
            "deflection_limit_in": span / 30.0,  # L/360, with span stored in feet.
            "additional_safety_factor": safety,
            "loads": [{"type": "uniform", "intensity_kip_ft": intensity,
                       "start_ft": start, "end_ft": end}],
        }

    def save_design(self):
        path = filedialog.asksaveasfilename(
            title="Save beam design", defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("All files", "*")),
        )
        if not path:
            return
        try:
            data = self._design_data()
            with open(path, "w", encoding="utf-8") as design_file:
                json.dump(data, design_file, indent=2)
                design_file.write("\n")
        except (OSError, ValueError, KeyError) as exc:
            messagebox.showerror("Could not save design", str(exc), parent=self)
            return
        self.status.configure(text=f"Design saved to {path}", foreground="#18704e")

    def save_results(self):
        if not self.results_current or self.last_result is None:
            messagebox.showinfo("Results need updating", "Press Calculate to update the results before saving them.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            title="Save analysis results", defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*")),
        )
        if not path:
            return
        result = self.last_result
        summary_keys = (
            "reaction_left_kip", "reaction_right_kip", "fixed_moment_kip_ft",
            "max_moment_kip_ft", "moment_at_ft", "max_deflection_in",
            "deflection_at_ft", "bending_stress_ksi", "bending_limit_ksi",
            "bending_pass", "deflection_limit_in", "deflection_pass",
        )
        design = self._design_data()
        load = design["loads"][0]
        metadata = {
            "support": design["support"],
            "span_ft": design["span_ft"],
            "section": design["section"],
            "additional_safety_factor": design["additional_safety_factor"],
            "deflection_limit_in": design["deflection_limit_in"],
            "load_intensity_kip_ft": load["intensity_kip_ft"],
            "load_start_ft": load["start_ft"],
            "load_end_ft": load["end_ft"],
            **{key: self._scalar_value(result[key]) for key in summary_keys},
        }
        diagram_columns = (
            ("position_ft", result["x_ft"]),
            ("shear_kip", result["shear_kip"]),
            ("moment_kip_ft", result["moment_kip_ft"]),
            ("deflection_in", result["deflection_in"]),
        )
        headers = list(metadata) + [name for name, _ in diagram_columns]
        try:
            with open(path, "w", encoding="utf-8", newline="") as results_file:
                writer = csv.DictWriter(results_file, fieldnames=headers)
                writer.writeheader()
                for index in range(len(result["x_ft"])):
                    row = metadata.copy() if index == 0 else {}
                    for name, values in diagram_columns:
                        row[name] = self._scalar_value(values[index])
                    writer.writerow(row)
        except (OSError, ValueError, KeyError) as exc:
            messagebox.showerror("Could not save results", str(exc), parent=self)
            return
        self.status.configure(text=f"Results saved to {path}", foreground="#18704e")

    def save_pdf(self):
        if not self.results_current or self.last_result is None:
            messagebox.showinfo("Results need updating", "Press Calculate to update the results before saving the calculation sheet.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            title="Save calculation sheet", defaultextension=".pdf",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*")),
        )
        if not path:
            return
        try:
            self._write_calculation_pdf(path)
        except (OSError, ValueError, KeyError) as exc:
            messagebox.showerror("Could not save PDF", str(exc), parent=self)
            return
        self.status.configure(text=f"Calculation sheet saved to {path}", foreground="#18704e")

    def _write_calculation_pdf(self, path):
        design = self._design_data()
        result = self.last_result
        load = design["loads"][0]
        figure = Figure(figsize=(8.5, 11), dpi=150)
        grid = figure.add_gridspec(12, 1, left=0.11, right=0.94, top=0.95, bottom=0.07, hspace=0.58)

        title_ax = figure.add_subplot(grid[0, 0])
        title_ax.axis("off")
        title_ax.text(0, 0.92, "BEAM CALCULATION SHEET", fontsize=17, weight="bold", color="#263b4a", va="top")
        title_ax.text(0, 0.12, "Beam Designer · Analysis summary", fontsize=9, color="#526574", va="bottom")

        inputs_ax = figure.add_subplot(grid[1:3, 0])
        inputs_ax.axis("off")
        inputs = [
            ["Support", design["support"], "Span", f'{design["span_ft"]:g} ft'],
            ["Section", design["section"], "Safety factor", f'{design["additional_safety_factor"]:g}'],
            ["Uniform load", f'{load["intensity_kip_ft"]:g} kip/ft', "Load extent", f'{load["start_ft"]:g}–{load["end_ft"]:g} ft'],
            ["Deflection limit", f'{design["deflection_limit_in"]:.3f} in (L/360)', "Bending basis", "Allowable stress / safety factor"],
        ]
        table = inputs_ax.table(cellText=inputs, colWidths=[0.19, 0.31, 0.19, 0.31], cellLoc="left", bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#d6dee4")
            if col in (0, 2):
                cell.set_facecolor("#edf2f5")
                cell.set_text_props(weight="bold", color="#263b4a")
            else:
                cell.set_facecolor("white")

        check_ax = figure.add_subplot(grid[3, 0])
        check_ax.axis("off")
        check_ax.text(0, 0.98, "DESIGN CHECKS", fontsize=10, weight="bold", color="#263b4a", va="top")
        bending_status = "PASS" if result["bending_pass"] else "FAIL"
        deflection_status = "PASS" if result["deflection_pass"] else "FAIL"
        check_ax.text(0.02, 0.57, f'BENDING  {bending_status}    {result["bending_stress_ksi"]:.3f} / {result["bending_limit_ksi"]:.3f} ksi', fontsize=9, weight="bold", color="#18704e" if result["bending_pass"] else "#b42318")
        check_ax.text(0.52, 0.57, f'DEFLECTION  {deflection_status}    {result["max_deflection_in"]:.3f} / {result["deflection_limit_in"]:.3f} in', fontsize=9, weight="bold", color="#18704e" if result["deflection_pass"] else "#b42318")
        check_ax.text(0.02, 0.12, f'Reactions: left {result["reaction_left_kip"]:.3f} kip · right {result["reaction_right_kip"]:.3f} kip', fontsize=8, color="#526574")

        beam_ax = figure.add_subplot(grid[4:6, 0])
        span = design["span_ft"]
        beam_ax.plot([0, span], [0, 0], color="#263b4a", lw=5, solid_capstyle="round")
        for px in np.linspace(load["start_ft"], load["end_ft"], max(5, int(span * 1.5))):
            beam_ax.annotate("", (px, 0.10), (px, 0.48), arrowprops={"arrowstyle": "->", "color": "#b04c37", "lw": 1})
        beam_ax.text((load["start_ft"] + load["end_ft"]) / 2, 0.54, f'{load["intensity_kip_ft"]:g} kip/ft', ha="center", fontsize=8, color="#b04c37")
        if design["support"] == "Simply supported":
            beam_ax.scatter([0, span], [-0.10, -0.10], marker="^", color="#176b87", s=48)
        else:
            beam_ax.plot([0, 0], [-0.28, 0.28], color="#176b87", lw=4)
        beam_ax.set_xlim(-span * 0.04, span * 1.04)
        beam_ax.set_ylim(-0.35, 0.72)
        beam_ax.set_title("BEAM AND LOADING", loc="left", fontsize=9, weight="bold", color="#263b4a", pad=3)
        beam_ax.axis("off")

        chart_specs = [
            (grid[6:8, 0], result["shear_kip"], "SHEAR", "kip", "#176b87"),
            (grid[8:10, 0], result["moment_kip_ft"], "MOMENT", "kip-ft", "#b04c37"),
            (grid[10:12, 0], result["deflection_in"], "DEFLECTION", "in", "#18704e"),
        ]
        for rows, values, label, unit, color in chart_specs:
            ax = figure.add_subplot(rows)
            ax.plot(result["x_ft"], values, color=color, lw=1.5)
            ax.axhline(0, color="#82919d", lw=0.6)
            ax.set_ylabel(unit, fontsize=7)
            ax.set_title(label, loc="left", fontsize=9, weight="bold", color="#263b4a", pad=2)
            ax.grid(alpha=0.18)
            ax.tick_params(labelsize=7)
        figure.axes[-1].set_xlabel("Position along span (ft)", fontsize=7)
        figure.savefig(path, format="pdf")

    @staticmethod
    def _scalar_value(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        return value

    def open_design(self):
        path = filedialog.askopenfilename(
            title="Open beam design",
            filetypes=(("JSON files", "*.json"), ("All files", "*")),
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as design_file:
                data = json.load(design_file)
            if not isinstance(data, dict) or data.get("format") != "beam-designer" or data.get("version") != 1:
                raise ValueError("This is not a supported Beam Designer JSON file.")
            span = float(data["span_ft"])
            fixed_limit = span / 30.0  # L/360, converted from feet to inches.
            stored_limit = float(data["deflection_limit_in"])
            if not np.isclose(stored_limit, fixed_limit, rtol=1e-9, atol=1e-9):
                raise ValueError("The file's deflection limit does not match the fixed L/360 limit.")
            support = data["support"]
            section = data["section"]
            if support not in ("Simply supported", "Cantilever"):
                raise ValueError("Unsupported support condition in design file.")
            if section not in MEMBERS:
                raise ValueError("The section in this design file is not available.")
            loads = data["loads"]
            if not isinstance(loads, list) or len(loads) != 1 or loads[0].get("type") != "uniform":
                raise ValueError("Design files must contain one uniform load.")
            load = loads[0]
            intensity = float(load["intensity_kip_ft"])
            start = float(load["start_ft"])
            end = float(load["end_ft"])
            safety = float(data.get("additional_safety_factor", 1.0))
            analyze(span, support, [UniformLoad(intensity, start, end)], MEMBERS[section], safety)
        except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
            messagebox.showerror("Could not open design", str(exc), parent=self)
            return

        values = {
            "Support": support,
            "Span (ft)": str(span),
            "Member": section,
            "Additional safety factor": str(safety),
            "Intensity": str(intensity),
            "Start (ft)": str(start),
            "End (ft)": str(end),
        }
        for name, value in values.items():
            self.vars[name].set(value)
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
        spacer = ttk.Frame(left)
        spacer.grid(sticky="nsew")
        left.rowconfigure(spacer.grid_info()["row"], weight=1)
        design_buttons = ttk.Frame(left)
        design_buttons.grid(sticky="ew", pady=(6, 0))
        for column in range(4):
            design_buttons.columnconfigure(column, weight=1, uniform="design_button")
        ttk.Button(design_buttons, text="Open…", command=self.open_design).grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=(0, 4))
        ttk.Button(design_buttons, text="Save…", command=self.save_design).grid(row=0, column=2, columnspan=2, sticky="ew", padx=(4, 0), pady=(0, 4))
        ttk.Button(design_buttons, text="Save Results", command=self.save_results).grid(row=1, column=0, columnspan=4, sticky="ew")
        ttk.Button(design_buttons, text="Save PDF", command=self.save_pdf).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(4, 0))
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
        self.results_current = False
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
            self.results_current = False
            self.status.configure(text=str(exc), foreground="#b42318")
            for ent in self.errors.values():
                ent.configure(style="Invalid.TEntry")
            self.style = ttk.Style(self)
            self.style.configure("Invalid.TEntry", fieldbackground="#ffd9d9")
            return
        for ent in self.errors.values():
            ent.configure(style="TEntry")
        self.last_result = result
        self.results_current = True
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
