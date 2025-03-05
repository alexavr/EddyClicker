from netCDF4 import Dataset
import numpy as np

# Подготовка данных
# cdo select,var=HGT /storage/kubrick/SMP6km/2021/wrfout_d01_2021-02-23_00.nc tmp.nc
# cdo seltimestep,1 tmp.nc tmp1.nc
# cdo --reduce_dim tmp1.nc tmp2.nc
# cdo chname,HGT,hgt tmp2.nc SMP6km_hgt.nc
# rm tmp*
#
# cp scp kubrick:/storage/kubrick/vkoshkina/data/SMP/R2D_SMP_smoothing/sigma_2_R2D_SMP_2021-02-23.nc .
# cdo merge geopotential.nc sigma_2_DBSCAN_SMP_level_20_2021-02-23.nc tmp.nc
# mv tmp.nc sigma_2_DBSCAN_SMP_level_20_2021-02-23.nc
#

# DATASET DESCRIPTION
RES = 'SMP'
PREF = '6km'

### MAIN VARIABLES

# GUI windows size
SCREEN_HEIGHT = 1000
WINDOW_WIDTH = 2000

LEVEL = 0  # Level of interest
RORTEX_VARNAME = 'R2D'  # Criteria to plot (contourf)
LOCAL_EXTR_VARNAME = 'local_extr_cluster'  # dots to plot (scatter)
SCALAR1_VARNAME = 'geopotential'  # help field (contour)
SCALAR2_VARNAME = 'WSPD'  # help field (at spacebar)
SCALAR1_LEVELS_STEP = 50  # contour interval
SCALAR1_LEVELS_FINE_STEP = 10  # contour interval view

TRACKS_FOLDER = 'track_folder'  # track output folder
FILE_RORTEX = "2019-01.nc"  # Input file
FILE_SAVE = f"test.txt"

# Get land map
ds_land = Dataset(FILE_RORTEX)
LAND = ds_land["HGT"][:, :]
LAND = np.where(LAND > 5, 0, np.nan)

# Level height at the title (km)
LEV_HGT = np.nanmean(ds_land["geopotential"][0, LEVEL, :, :]) / 10 / 1000
ds_land.close()

# Map settings
from pyproj import Geod

GEOD = Geod(ellps="WGS84")
PHI = np.linspace(0, 2 * np.pi, 100)

# FOR POSTPROCESSING (CHECK TRACK)
NRADIUS = 100
NTHETA = 36
