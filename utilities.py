'''
Utility module with few number of math fuctions.
It's used for constraction of propagation chaines
by click on fronts
'''


from math import sqrt
from bisect import bisect_left


def vector_sum(v_1, v_2):
    return [c1 + c2 for c1, c2 in zip(v_1, v_2)]


def vector_sub(v_1, v_2):
    return [c1 - c2 for c1, c2 in zip(v_1, v_2)]


def vector_multiply(const, vector):
    return [const * c for c in vector]


def vector(point_start, point_end):
    return [c2 - c1 for c1, c2 in zip(point_start, point_end)]


def vector_len(vector):
    return sqrt(sum([c ** 2 for c in vector]))


def vector_unit(vector):
    v_len = vector_len(vector)
    return [c / v_len for c in vector]


def dot_product(v1, v2):
    return sum([coo1 * coo2 for coo1, coo2 in zip(v1, v2)])


def cross_product(v1, v2):
    return [v1[1] * v2[2] - v1[2] * v2[1], v1[2] * v2[0] - v1[0] * v2[2], v1[0] * v2[1] - v1[1] * v2[0]]


def project_point_on_axis(point, p1, p2):
    v_aux = [dot_product(vector(p1, point), vector_unit(vector(p1, p2))) * coo for coo in vector_unit(vector(p1, p2))]
    return vector_sum(p1, v_aux)


def distance_between_points(p1, p2):
    return sqrt(sum([(coo1 - coo2)**2 for coo1, coo2 in zip(p1, p2)]))


def distance_point_axis(point, p1, p2):
    return distance_between_points(point, project_point_on_axis(point, p1, p2))


def check_point_over_segment(point, p1, p2):
    segment_vector = vector(p1, p2)
    return dot_product(segment_vector, vector(p1, point)) * dot_product(segment_vector, vector(p2, point)) <= 0


def lin_interp(x_, ps):
    if x_ >= ps[-1][0]:
        return ps[-1][1]
    elif x_ <= ps[0][0]:
        return ps[0][1]
    else:
        i = bisect_left([p[0] for p in ps], x_)
        return ps[i - 1][1] + (ps[i][1] - ps[i - 1][1]) * (x_ - ps[i - 1][0]) / (ps[i][0] - ps[i - 1][0])
