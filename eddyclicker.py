import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.interpolate import RectBivariateSpline
import datetime as dt
from glob import glob
from shutil import move
from os.path import isfile, isdir
from os import mkdir
from track import *
from const import *


# kill -9 $(ps ax | grep eddy | cut -f1 -d' ' | head -1)


def show_instructions():
    instructions = (
        "Welcome to EddyClicker!\n\n"
        "Instruction:\n"
        "↑ - move to next stamp\n"
        "↓ - move to prev stamp\n"
        "LMC - select the point\n"
        "Esc - release the point\n"
        "RMC - save the track\n"
        "2xLMC - pop the point\n\n"
        "Enjoy it!"
    )
    messagebox.showinfo("Instruction", instructions)


class MapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EddyClicker")

        screen_height = self.winfo_screenheight()
        window_width = int(screen_height * WIN_SCALE)
        x_offset = 0
        y_offset = 0
        self.geometry(f"{window_width}x{screen_height}+{x_offset}+{y_offset}")
        self.resizable(False, False)
        # self.geometry("1000x1000")

        if first_time:
            show_instructions()

        # Create main container
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create toolbar frame
        toolbar_frame = tk.Frame(container)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        self.time_entry = tk.Entry(container)
        self.time_entry.insert(0, "YYYY-MM-DD-HH")
        self.time_entry.pack(side=tk.TOP)
        self.time_entry.bind("<Return>", self.update_time)

        # Create figure frame
        figure_frame = tk.Frame(container)
        figure_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.path_file_rortex = FILE_RORTEX
        self.path_save_file = TRACKS_FOLDER

        if not isfile(FILE_RORTEX):
            self.select_file_rortex()

        if not isdir(TRACKS_FOLDER):
            mkdir(TRACKS_FOLDER)

        self.file_rortex = Dataset(self.path_file_rortex)
        self.centers = self.file_rortex[LOCAL_EXTR_VARNAME][:, :, :]

        self.shot = 0
        self.rortex = None
        self.scalar = None
        self.curr_centers = None
        self.prev_centers = None
        self.curr_line = None
        self.prev_point = None
        self.curr_point = None
        self.el_p1 = None
        self.el_p2 = None
        self.el_p3 = None
        self.prev_el = None
        self.curr_el = None
        self.sel_el = False
        self.back = "contour"
        self.k = 1
        self.tracks = []

        if len(self.file_rortex["XLAT"].shape) == 3:
            ydim = self.file_rortex["XLAT"].shape[1]
            xdim = self.file_rortex["XLAT"].shape[2]
        elif len(self.file_rortex["XLAT"].shape) == 2:
            ydim = self.file_rortex["XLAT"].shape[0]
            xdim = self.file_rortex["XLAT"].shape[1]
        else:
            exit("STOP! Wrong XLAT/XLONG dimentions")

        self.lat_int = RectBivariateSpline(np.arange(ydim), np.arange(xdim), self.file_rortex["XLAT"][:, :])
        self.lon_int = RectBivariateSpline(np.arange(ydim), np.arange(xdim), self.file_rortex["XLONG"][:, :])
        self.mesh_lon, self.mesh_lat = np.meshgrid(np.arange(ydim), np.arange(xdim))

        # Create figure and canvas
        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=figure_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Connect events
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.bind("<Down>", self.go_back)
        self.bind("<Up>", self.go_forward)
        self.bind("<Escape>", self.release_track)
        self.bind("<space>", self.change_back)
        self.focus_set()

        if self.path_save_file:
            self.load_tracks(self.path_save_file)
        self.create_map()

    def create_map(self):
        remove_collections(self.rortex)
        if self.back == "contour":
            remove_collections(self.scalar)
        else:
            remove_streamline(self.scalar)

        if self.curr_centers:
            if self.prev_centers:
                self.prev_centers.remove()
            self.prev_centers = self.curr_centers.get_offsets()
            self.prev_centers = self.ax.scatter(self.prev_centers[:, 0], self.prev_centers[:, 1], c="k", zorder=5,
                                                s=30)
            self.curr_centers.remove()

        self.ax.contourf(self.mesh_lon, self.mesh_lat, LAND, colors="LightGrey")

        if self.back == "contour":
            self.scalar = self.ax.contour(self.mesh_lon, self.mesh_lat,
                                          self.file_rortex[SCALAR_VARNAME][self.shot, 0, :, :],
                                          levels=SCALAR_LEVELS, alpha=0.7, colors="k", linewidths=0.2)
        else:
            self.scalar = self.ax.streamplot(self.mesh_lon, self.mesh_lat,
                                             self.file_rortex[VELOCITY_VARNAME[0]][self.shot, 0, :, :],
                                             self.file_rortex[VELOCITY_VARNAME[1]][self.shot, 0, :, :],
                                             color="k", linewidth=0.4, arrowsize=0, density=3)

        rortex = self.file_rortex[RORTEX_VARNAME][self.shot, 0, :, :]
        rortex = np.where(rortex <= 0, np.nan, rortex)
        self.rortex = self.ax.contourf(self.mesh_lon, self.mesh_lat, rortex, levels=10, cmap="gnuplot_r", alpha=0.8)

        mask = self.centers[self.shot, 0, :, :] > 0
        self.curr_centers = self.ax.scatter(self.mesh_lon[mask], self.mesh_lat[mask], facecolor="None", edgecolor="k",
                                            zorder=6, s=100, lw=2)

        self.ax.set_title((dt.datetime(year=1979, month=1, day=1) + dt.timedelta(
            minutes=int(self.file_rortex["Time"][self.shot]))).strftime("%d.%m.%Y %H:%M"), fontsize=20)
        self.ax.format_coord = self.custom_format_coord
        self.canvas.draw()

    def update_time(self, event):
        time_str = self.time_entry.get()
        try:
            target_time = (dt.datetime.strptime(time_str, "%Y-%m-%d-%H") - dt.datetime(year=1979, month=1,
                                                                                       day=1)).total_seconds() / 60
            self.shot = int(np.argmin(np.abs(target_time - np.array(self.file_rortex["XTIME"][:]))))
            self.create_map()

        except ValueError:
            messagebox.showerror("Error", "Wrong time format. Please, use YYYY-MM-DD-HH")

    def go_back(self, event=None):
        if self.shot > 0:
            self.shot -= 1
        self.create_map()

    def go_forward(self, event=None):
        if self.shot < len(self.file_rortex["Time"][:]) - 1:
            self.shot += 1
        self.create_map()

    def release_track(self, event=None):
        if self.prev_point:
            self.prev_point = None
        if self.curr_point:
            self.curr_point = None
        if self.curr_line:
            self.curr_line.remove()
            self.curr_line = None
        if self.curr_el:
            if self.curr_el.plot:
                self.curr_el.plot.remove()
            if self.curr_el.points:
                self.curr_el.points.remove()
            self.curr_el = None
        if self.el_p1:
            self.el_p1.clean()
            self.el_p1 = None
        if self.el_p2:
            self.el_p2.clean()
            self.el_p2 = None
        if self.el_p3:
            self.el_p3.clean()
            self.el_p3 = None
        self.canvas.draw()

    def change_back(self, event=None):
        if self.back == "contour":
            remove_collections(self.scalar)
            self.back = "stream"
        else:
            remove_streamline(self.scalar)
            self.back = "contour"
        self.scalar = None
        self.create_map()

    def custom_format_coord(self, x, y):
        return f"x = {x:.0f}, y = {y:.0f}; Lat = {self.lat_int(x, y)[0, 0]:.2f}°, Lon = {self.lon_int(x, y)[0, 0]:.2f}°"

    def change_path(self, file_path, name):
        with open("const.py", "r") as fin:
            with open("tmp.py", "w") as fout:
                for line in fin.readlines():
                    if name in line:
                        line = line.replace(line.split(" = ")[-1], f"'{file_path}'\n")
                    fout.write(line)
        move("tmp.py", "const.py")

    # def select_file_scalar(self):
    #     file_path = filedialog.askopenfilename(initialdir="/".join(FILE_SCALAR.split("/")[:-1]),
    #                                            title="Select criteria file", filetypes=[("NetCDF files", "*.nc")])
    #     if file_path:
    #         self.path_file_scalar = file_path
    #         self.file_scalar = Dataset(self.path_file_scalar)
    #         self.create_map()
    #         self.change_path(file_path, "FILE_SCALAR")

    def select_file_rortex(self):
        file_path = filedialog.askopenfilename(initialdir="/".join(FILE_RORTEX.split("/")[:-1]),
                                               title="Select centers file", filetypes=[("NetCDF files", "*.nc")])
        if file_path:
            self.path_file_rortex = file_path
            ds = Dataset(self.path_file_rortex)
            self.centers = ds["center"][:, 0, :, :]
            ds.close()
            self.create_map()
            self.change_path(file_path, "FILE_RORTEX")

    def select_save_folder(self):
        folder_path = filedialog.askdirectory(initialdir="/".join(TRACKS_FOLDER.split("/")[:-1]),
                                              title="Select save folder")
        if folder_path:
            self.path_save_file = folder_path
            self.change_path(folder_path, "TRACKS_FOLDER")

    def on_click(self, event):
        if event.inaxes != self.ax or event.dblclick:
            return

        if event.button == 1:
            if not self.prev_point:  # no first point
                cent_f, cent = self.is_center(event.xdata, event.ydata, -1)  # coordinates of center around 2 px
                if cent_f:
                    self.prev_point = cent
                    print("first point selected")
                # cent_track = self.in_track(self.prev_point)
                # if cent_track == -1:
                #     self.sel_el = True  # start of new track

            else:  # have first point
                if not self.curr_point:
                    cent_f, cent = self.is_center(event.xdata, event.ydata, 0)  # coordinates of center around 2 px
                    if cent_f:
                        self.curr_point = cent
                        self.sel_el = True
                        print("second point selected")

                else:  # have two points
                    cent_track = self.in_track(self.prev_point)

                    if self.el_p1 is None:
                        self.el_p1 = DrawPoint(event.xdata, event.ydata,
                                               self.ax)  # np.array([event.xdata, event.ydata])
                        self.el_p1.draw()
                    elif self.el_p2 is None:
                        self.el_p2 = DrawPoint(event.xdata, event.ydata,
                                               self.ax)  # np.array([event.xdata, event.ydata])
                        self.el_p2.draw()
                    elif self.el_p3 is None:
                        self.el_p3 = DrawPoint(event.xdata, event.ydata,
                                               self.ax)  # np.array([event.xdata, event.ydata])
                        self.el_p3.draw()

                        ell = Ellipse(self.curr_point.t, self.curr_point.x, self.curr_point.y,
                                      self.el_p1, self.el_p2, self.el_p3, self.ax)

                        if cent_track == -1:
                            print(f"created {len(self.tracks)} track")
                            new_track = Track(len(self.tracks), self.ax)
                            new_track.points.append(Ellipse(self.prev_point.t, self.prev_point.x, self.prev_point.y,
                                                            np.array([self.prev_point.x, self.prev_point.y]),
                                                            np.array([self.prev_point.x, self.prev_point.y]),
                                                            np.array([self.prev_point.x, self.prev_point.y]),
                                                            self.ax))
                            new_track.points.append(ell)
                            self.tracks.append(new_track)
                            self.tracks[-1].draw()
                        else:
                            print(f"appended {len(self.tracks[cent_track].points)} point to {cent_track} track")
                            self.tracks[cent_track].append(ell)
                            self.tracks[-1].draw()

                        self.prev_point = None
                        self.curr_point = None
                        self.el_p1.clean()
                        self.el_p2.clean()
                        self.el_p3.clean()
                        self.el_p1 = None
                        self.el_p2 = None
                        self.el_p3 = None

        elif event.button == 3 and self.prev_point is None:
            cent_f, cent = self.is_center(event.xdata, event.ydata, -1)
            if cent_f:
                cent_track = self.in_track(cent)
                self.ask_to_save_track(cent_track)

        elif event.dblclick and event.inaxes == self.ax:
            cent_f, cent = self.is_center(event.xdata, event.ydata, -1)
            if cent_f:
                cent_track = self.in_track(cent)
                if cent_track != -1:
                    point_index = -1
                    for i, p in enumerate(self.tracks[cent_track].points):
                        if p.x0 == cent.x and p.y0 == cent.y:
                            point_index = i
                            break
                    if point_index != -1:
                        self.tracks[cent_track].points.pop(point_index)
                        self.tracks[cent_track].draw()
                        self.canvas.draw()
        self.canvas.draw()

    def on_mouse_move(self, event):

        if self.prev_point and self.curr_point is None and event.inaxes == self.ax:
            if self.curr_line:
                self.curr_line.remove()
            self.curr_line = \
                self.ax.plot([self.prev_point.x, event.xdata], [self.prev_point.y, event.ydata], c="k", lw=1)[0]
        self.canvas.draw_idle()

    def is_center(self, x, y, c=0):
        mask = self.centers[self.shot + c, 0, :, :] > 0
        centers = np.column_stack((self.mesh_lon[mask], self.mesh_lat[mask]))
        for center in centers:
            if np.isclose([x, y], center, atol=2).all():
                return True, Point(self.shot + c, center[0], center[1])
        return False, Point(-1, -1, -1)

    def in_track(self, point):
        for track in self.tracks:
            if track != 0 and track is not None:
                if track.points[-1].x0 == point.x and track.points[-1].y0 == point.y:
                    return track.index
        return -1

    def ask_to_save_track(self, index):
        response = messagebox.askyesnocancel("Save Track", "Do you want to save this track?")
        if response is not None:
            if response:
                for p in self.tracks[index].points:
                    self.centers[p.t, 0, p.y0, p.x0] = np.nan
                self.tracks[index].save()
                messagebox.showinfo("Saving", f"Track was saved into {self.path_save_file}/{index:09d}.csv")

            if not response:
                for po in self.tracks[index].points:
                    if po.plot and po.plot in self.ax.lines:
                        po.plot.remove()
                if self.tracks[index].plot and self.tracks[index].plot in self.ax.lines:
                    self.tracks[index].plot.remove()
                for p in self.tracks[index].points:
                    if p and p in self.ax.collections:
                        p.remove()
                self.tracks[index] = None

            self.curr_point = None
            self.prev_point = None
            if self.curr_line:
                self.curr_line.remove()
                self.curr_line = None
            if self.curr_el:
                if self.curr_el.plot:
                    self.curr_el.plot.remove()
                if self.curr_el.points:
                    self.curr_el.points.remove()
                self.curr_el = None

    def load_tracks(self, path):
        files = sorted(glob(path + "/[!~$]*.csv"))
        for f in files:
            df = pd.read_csv(f)
            self.centers[df['time_ind'].astype('int64'), :,
            df['pyc_ind'].astype('int64'), df['pxc_ind'].astype('int64')] = np.nan
            self.tracks.append(0)
        self.canvas.draw()


if __name__ == "__main__":
    app = MapApp()
    app.mainloop()
