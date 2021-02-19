from tina.engine import *


@ti.data_oriented
class PreviewEngine(metaclass=Singleton):
    def __init__(self):
        DefaultSampler()

    def get_rng(self, i, j):
        return DefaultSampler().get_proxy(wanghash2(i, j))

    def render(self):
        DefaultSampler().update()
        self._render()

    @ti.kernel
    def _render(self):
        for i, j in ti.ndrange(FilmTable().nx, FilmTable().ny):
            Stack().set(i * FilmTable().nx + j)
            rng = self.get_rng(i, j)

            albedo = V3(0.0)
            normal = V3(0.0)

            dx, dy = random2(rng)
            x = (i + dx) / FilmTable().nx * 2 - 1
            y = (j + dy) / FilmTable().ny * 2 - 1
            ray = Camera().generate(x, y)
            hit = BVHTree().intersect(ray, -1)

            if hit.hit == 1:
                hitpos, normal, sign, material = ModelPool().get_geometries(hit, ray)
                albedo = V3(1.0)

            FilmTable()[1, i, j] += V34(albedo, 1.0)
            FilmTable()[2, i, j] += V34(normal, 1.0)

            Stack().unset()