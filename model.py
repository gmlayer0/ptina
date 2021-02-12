from allocator import *
from geometries import *


@ti.data_oriented
class ModelPool(metaclass=Singleton):
    is_taichi_class = True

    def __init__(self, size=2**20, count=2**6):
        self.mman = MemoryAllocator(size)
        self.idman = IdAllocator(count)
        self.beg = ti.field(int, count)
        self.size = ti.field(int, count)
        self.root = ti.field(float, size)

    @ti.kernel
    def get_nverts(self) -> int:
        ret = 0
        for i in range(self.size.shape[0]):
            ret += self.size[i]
        return ret

    @ti.func
    def subscript(self, i):
        return tovector([self.root[i * 8 + j] for j in range(8)])

    @ti.func
    def get_face(self, i):
        a0 = self[i + 0]
        a1 = self[i + 1]
        a2 = self[i + 2]
        v0 = V(a0[0], a0[1], a0[2])
        vn0 = V(a0[3], a0[4], a0[5])
        vt0 = V(a0[6], a0[7])
        v1 = V(a1[0], a1[1], a1[2])
        vn1 = V(a1[3], a1[4], a1[5])
        vt1 = V(a1[6], a1[7])
        v2 = V(a2[0], a2[1], a2[2])
        vn2 = V(a2[3], a2[4], a2[5])
        vt2 = V(a2[6], a2[7])
        return Face(v0, v1, v2, vn0, vn1, vn2, vt0, vt1, vt2)

    @ti.kernel
    def _to_numpy(self, id: int, arr: ti.ext_arr()):
        beg, end = self.beg[id], self.beg[id] + self.size[id]
        for i in range(beg, end):
            for k in ti.static(range(8)):
                arr[i - beg, k] = self[i][k]

    def to_numpy(self, id):
        arr = np.empty((self.size[id], 8), dtype=np.float32)
        self._to_numpy(id, arr)
        return arr

    @ti.kernel
    def from_numpy(self, id: int, arr: ti.ext_arr()):
        beg, end = self.beg[id], self.beg[id] + self.size[id]
        for i in range(beg, end):
            for k in ti.static(range(8)):
                self[i][k] = arr[i - beg, k]

    def new(self, nverts):
        id = self.idman.malloc()
        base = self.mman.malloc(nverts)
        self.beg[id] = base
        self.size[id] = nverts
        return id

    def delete(self, id):
        base = self.base[id]
        self.idman.free(id)
        self.mman.free(base)

    def load(self, arr):
        if isinstance(arr, str):
            from tools.readobj import readobj
            arr = readobj(arr)

        if isinstance(arr, dict):
            verts = arr['v'][arr['f'][:, :, 0]]
            norms = arr['vn'][arr['f'][:, :, 2]]
            coors = arr['vt'][arr['f'][:, :, 1]]
            verts = verts.reshape(arr['f'].shape[0] * 3, 3)
            norms = norms.reshape(arr['f'].shape[0] * 3, 3)
            coors = coors.reshape(arr['f'].shape[0] * 3, 2)
            arr = np.concatenate([verts, norms, coors], axis=1)

        if arr.dtype == np.float64:
            arr = arr.astype(np.float32)

        nverts = arr.shape[0]

        id = self.new(nverts)
        self.from_numpy(id, arr)
        return id


if __name__ == '__main__':
    ti.init(print_ir=True)
    ModelPool()

    im = ModelPool().load('assets/monkey.obj')
    print(ModelPool().to_numpy(im))
