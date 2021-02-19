from tina.stack import *
from tina.camera import *
from tina.acceltree import *
from tina.image import *
from tina.model import *
from tina.light import *
from tina.worldlight import *
from tina.mtllib import *
from tina.filmtable import *


def init_things():
    Stack()
    Camera()
    BVHTree()
    ImagePool()
    ModelPool()
    LightPool()
    WorldLight()
    MaterialPool()
    FilmTable()
