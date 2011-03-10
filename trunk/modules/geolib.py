import math

DEFAULT_GRID_LEN = 1.0
MIN_GRID_LEN = 0.01

# Base latitude and longtitude is so selected that it is
# a 10m x 10m square on (36.87N, 0.0E)
BASE_LAT = 0.000089877
BASE_LON = 0.000112346
EARTH_RADIUS = 6378.137
MIN_RES = 0.0000001

# BIT patterns used on grid id
SCALE_MASK = ((1<<16)-1) << 48
LAT_MASK = ((1<<24)-1) << 24
LON_MASK = (1<<24)-1

class GeoPt(object):
    def __init__(self, lat, lon=None):
        if not lon and isinstance(lat, basestring):
            pair = lat.split(',')
            lat = float(pair[0])
            lon = float(pair[1])

            if not self.verify_geo_pt(lat, lon):
                raise Exception('lat/lon (%f/%f) is out of range!' % (lat, lon))

            self.lat = lat
            self.lon = lon
        elif lat and lon and isinstance(lat, float) and isinstance(lon, float):
            if not self.verify_geo_pt(lat, lon):
                raise Exception('lat/lon (%f/%f) is out of range!' % (lat, lon))

            self.lat = lat
            self.lon = lon
        else:
            raise Exception('float lat/lon or str expression expected!')

    def verify_geo_pt(self, lat, lon):
        return abs(lat) <= 90 and abs(lon) <= 180

class GeoGrid(object):
    """
    A GeoGrid represents a rectangle-like area on the surface of earth.
    The lat/lon of South-west corner of the rectangle is
    lat = 90 + BASE_LAT * scale * lat_index
    lon = 180 + BASE_LON * scale * lon_index

    The width (east-west length) and height(north-south length) of the rectangle is
    width = 10m * scale * cos(lat) * 1.25
    height = 10m * scale

    """

    def __init__(self, factory, lat_ind, lon_ind):
        self.factory = factory
        self.lat_ind = lat_ind
        self.lon_ind = lon_ind

        self.lat = factory.lat_factor * lat_ind - 90
        self.lon = factory.lon_factor * lon_ind - 180

    def get_id(self):
        """
        grid id is an long integer which encode the scale and index of a grid
        The format of a grid id is:
        001....010  001....100  010....000
        | 16bits |  | 24bits |  | 24bits |
          scale      lat index   lon index
        """
        return (self.factory.scale << 48) + (self.lat_ind << 24) + self.lon_ind
    
class GridFactory(object):
    factories = {}

    def __init__(self, scale=500):
        """
        scale is a number between 1~65535. It tells how large the grid is.
        scale == 1 means that a grid is a 10m x 10m square on 36.87N.
        """
        if scale < 1 or scale > 32767:
            raise Exception('scale should be a positive interger less than 32767!')

        if scale in GridFactory.factories:
            raise Exception('Do not use contructor to get a GridFactory. Use get_factory method instead!')

        self.scale = scale
        self.lat_factor = BASE_LAT * scale
        self.lon_factor = BASE_LON * scale

    def find_enclosure(self, pt):
        if not isinstance(pt, GeoPt):
            raise TypeError('GeoPt object expected!')
        
        lat_ind = int(math.floor((pt.lat + 90) / self.lat_factor))
        lon_ind = int(math.floor((pt.lon + 180) / self.lon_factor))

        return GeoGrid(self, lat_ind, lon_ind)

    @classmethod
    def id2grid(cls, grid_id):
        if isinstance(grid_id, long):
            gid = grid_id
        elif isinstance(grid_id, basestring):
            gid = long(grid_id)
        else:
            raise TypeError('long type or string type expected for grid_id')

        scale = (grid_id & SCALE_MASK) >> 48
        lat_index = (grid_id & LAT_MASK) >> 24
        lon_index = grid_id & LON_MASK

        factory = cls.get_factory(scale)
        return GeoGrid(factory, lat_index, lon_index)

    @classmethod
    def get_factory(cls, scale=500):
        factory = GridFactory.factories.get(scale)
        if not factory:
            factory = GridFactory(scale)
            GridFactory.factories[scale] = factory

        return factory

