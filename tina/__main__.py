from tina.engine import *
from tina.tools.control import *
from tina.tools.readgltf import readgltf


ti.init(ti.opengl)
Stack()
Camera()
BVHTree()
ImagePool()
ModelPool()
LightPool()
ToneMapping()
PathEngine()

#LightPool().color[0] = V3(4)
#LightPool().pos[0] = V(0, 0, 4)
#LightPool().radius[0] = 1.0
#LightPool().count[None] = 1

#mesh = ti.readobj('assets/cube.obj')
vertices, mtlids, materials = readgltf('assets/cornell.gltf')
print(mtlids)
print(len(mtlids), 'triangles')
ModelPool().load(vertices, mtlids)

BVHTree().build()

gui = ti.GUI()
gui.control = Control(gui)
while gui.running:
    if gui.control.process_events():
        #PathEngine().normal.clear()
        PathEngine().film.clear()
    Camera().set_perspective(gui.control.get_perspective())
    PathEngine().render()
    #PathEngine().render_aov()
    #gui.set_image(PathEngine().normal.to_numpy_normalized() * 0.5 + 0.5)
    gui.set_image(PathEngine().film.get_image())
    gui.show()
