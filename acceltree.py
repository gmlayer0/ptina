from model import *
from geometries import *
from stack import *


@ti.data_oriented
class _BVHTree:
    def __init__(self, size):
        self.size = size
        self.dir = ti.field(int, size)
        self.ind = ti.field(int, size)
        self.min = ti.Vector.field(3, float, size)
        self.max = ti.Vector.field(3, float, size)

    def build(self, pmin, pmax):
        assert len(pmin) == len(pmax)
        assert np.all(pmax >= pmin)
        data = lambda: None
        data.dir = self.dir.to_numpy()
        data.dir[:] = -1
        data.min = self.min.to_numpy()
        data.max = self.max.to_numpy()
        data.ind = self.ind.to_numpy()
        print('[Tina] building tree...')
        self._build(data, pmin, pmax, np.arange(len(pmin)), 1)
        self._build_from_data(data.dir, data.min, data.max, data.ind)
        print('[Tina] building tree done')

    @ti.kernel
    def _build_from_data(self,
            data_dir: ti.ext_arr(),
            data_min: ti.ext_arr(),
            data_max: ti.ext_arr(),
            data_ind: ti.ext_arr()):
        for i in range(self.dir.shape[0]):
            if data_dir[i] == -1:
                continue
            self.dir[i] = data_dir[i]
            for k in ti.static(range(3)):
                self.min[i][k] = data_min[i, k]
                self.max[i][k] = data_max[i, k]
            self.ind[i] = data_ind[i]

    def _build(self, data, pmin, pmax, pind, curr):
        assert curr < self.size, curr
        if not len(pind):
            return

        elif len(pind) <= 1:
            data.dir[curr] = 0
            data.ind[curr] = pind[0]
            data.min[curr] = pmin[0]
            data.max[curr] = pmax[0]
            return

        bmax = np.max(pmax, axis=0)
        bmin = np.min(pmin, axis=0)
        dir = np.argmax(bmax - bmin)
        sort = np.argsort(pmax[:, dir] + pmin[:, dir])
        mid = len(sort) // 2
        lsort = sort[:mid]
        rsort = sort[mid:]

        lmin, rmin = pmin[lsort], pmin[rsort]
        lmax, rmax = pmax[lsort], pmax[rsort]
        lind, rind = pind[lsort], pind[rsort]
        data.dir[curr] = 1 + dir
        data.ind[curr] = 0
        data.min[curr] = bmin
        data.max[curr] = bmax
        self._build(data, lmin, lmax, lind, curr * 2)
        self._build(data, rmin, rmax, rind, curr * 2 + 1)

    @ti.func
    def element_intersect(self, index, ray):
        return ModelPool().get_face(index).intersect(ray)

    @ti.func
    def intersect(self, ray, avoid):
        stack = Stack().get()
        ntimes = 0
        stack.clear()
        stack.push(1)
        ret = namespace(hit=0, depth=inf, index=-1, uv=V(0., 0.))

        while ntimes < self.size and stack.size() != 0:
            curr = stack.pop()

            if self.dir[curr] == 0:
                index = self.ind[curr]
                if index != avoid:
                    hit = self.element_intersect(index, ray)
                    if hit.hit != 0 and hit.depth < ret.depth:
                        ret.depth = hit.depth
                        ret.index = index
                        ret.uv = hit.uv
                        ret.hit = 1
                continue

            boxhit = Box(self.min[curr], self.max[curr]).intersect(ray)
            if boxhit.hit == 0:
                continue

            ntimes += 1
            stack.push(curr * 2)
            stack.push(curr * 2 + 1)

        return ret


@ti.data_oriented
class BVHTree(metaclass=Singleton):
    def __init__(self, size=2**20):
        self.core = _BVHTree(size)

    @ti.kernel
    def _dump_face_bboxes(self, nfaces: int, pmin: ti.ext_arr(), pmax: ti.ext_arr()):
        for i in range(nfaces):
            bbox = ModelPool().get_face(i).getbbox()
            for k in ti.static(range(3)):
                pmin[i, k] = bbox.lo[k]
                pmax[i, k] = bbox.hi[k]

    def build(self):
        nverts = ModelPool().get_nverts()
        nfaces = nverts // 3
        pmin = np.empty((nfaces, 3))
        pmax = np.empty((nfaces, 3))
        self._dump_face_bboxes(nfaces, pmin, pmax)
        self.core.build(pmin, pmax)

    @ti.func
    def intersect(self, ray, avoid):
        return self.core.intersect(ray, avoid)
