# EddyClicker

Project for manual eddies tracking written by Elizaveta Ezhova (October, 2024).

## Installing

All packages are listed in requirements.txt, so you can install it using pip or Anaconda.

```sh
conda create --name clicker_env
conda activate clicker_env
conda install --yes --file requirements.txt
python eddyclicker.py
```

```sh
python -m venv clicker_env
source clicker_env/bin/activate
pip install -r requirements.txt
python eddyclicker.py
```

## Using

### Data Preprocessing
The input file should be one has to contain all necessary data:
* 1d (time)     : XTIME as linux epoch ('XXX since 1979-01-01')
* 2d (y,x)      : XLAT, XLONG
* 3d (time,y,x) : Rortex field, scalar field (ex. geopotential), coordinates of Rortex extremes, second plot field (WSPD, CF, etc)

*Details will come later*


### First start

Edit the `const.file`:

```python
# DATASET DESCRIPTION (not nesesary )
RES  = 'SMP'
PREF = '6km'

### MAIN VARIABLES

# GUI windows size
SCREEN_HEIGHT = 650
WINDOW_WIDTH = 1200

LEVEL = 0                   # Level of interest
RORTEX_VARNAME = 'R2D'      # Criteria to plot (contourf)
LOCAL_EXTR_VARNAME = 'local_extr_cluster'   # dots to track (scatter)
SCALAR1_VARNAME = 'geopotential'            # help field (contour)
SCALAR1_LEVELS_STEP = 50                    # contour interval
SCALAR1_LEVELS_FINE_STEP = 10               # contour interval view
SCALAR2_VARNAME = 'WSPD'                    # help field (at spacebar)

TRACKS_FOLDER = 'track_folder'  # Output folder for track files
FILE_RORTEX = '2019-01.nc'      # Input file
FILE_SAVE = f'test.txt'

# Get land map
ds_land = Dataset(FILE_RORTEX)
LAND = ds_land["HGT"][ :, :]
LAND = np.where(LAND > 5, 0, np.nan)

# Level height (km) at the title. Needed ones
LEV_HGT = np.nanmean(
    ds_land["geopotential"][0, LEVEL, :, :]) / 10 / 1000
ds_land.close()

# Map settings
from pyproj import Geod
GEOD = Geod(ellps="WGS84")
PHI = np.linspace(0, 2 * np.pi, 100)

first_time = False

# CIRCLE SETTINGS FOR POSTPROCESSING (CHECK TRACK)
NRADIUS = 100
NTHETA = 36

```


### Navigation

* `↑` - move to next stamp
* `↓` - move to prev stamp
* `LMC` - select the point
* `Esc` - undo the last action
* `RMC` - save the track
* `2xLMC` - pop the point
* `spase` - switch to addinional field (`SCALAR2`) and back
* `cntr + z` - undo the last ellipse and track segment at ones
* Upper level field - time to jump instantly

You can also use matplotlib build-in buttons to ZOOM and MOVE the plot.

### Tracking

Strongly suggested to track one vortice at the time!

The current time step is written at the title. Using up and down keys on the keyboard you can move forward and backward in time. The current coordinates of the centers of the identified vortices are shown as black dots, the previous ones - as circles. To draw track you need to connect black dot to the circle.

Then you will have 3 left mouse clicks to mark the size of the vortice (as ellipse). The first to clicks are for the long axis of the ellips, the third click -- for the shot axis. All marked as blue dots.

You can create tracks by connecting points on the map in sequence. To create a track, you must connect a circle to a point - this will be the first segment. Then you need to make an ellipse around the structure, it can be done by 3 right-clicks. The first two clicks indicate the major axis, the third click would be the point at the minor axis. When you want to finish the track, right-click on the end point of the track (circle). The geographic coordinates of all points of the track will be sequentially written to the specified file in the `TRACKS_FOLDER` folder. After that, the built track will be deleted from the map.

Click of the last black dot point with LMC to save (`YES`) or delete (`NO`). If you realized you messed up the track -- you can just delete (`NO`) the track and start over.