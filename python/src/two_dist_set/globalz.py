__author__ = 'chaoweichen'

v = None
k = None
l = None
u = None

def set_problem(vv,kk,ll,uu):
    assert (vv-kk-1) * uu == kk*(kk-ll-1)
    global v, k, l, u
    v, k, l, u = vv, kk, ll, uu
    print('globalz.set_problem',v,k,l,u)

def generate_seed():
    return 2**(v-1) - 2**(v-k-1),  # tuple of numbers
