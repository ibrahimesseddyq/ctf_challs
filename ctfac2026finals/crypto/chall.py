import random

q = 65537
n = 15
m = 17
B = 16

class Q:
    def __init__(self, a, b, c, d):
        self.val = (a % q, b % q, c % q, d % q)
    def __add__(self, o):
        return Q(*[(x+y)%q for x,y in zip(self.val, o.val)])
    def __mul__(self, o):
        a1,b1,c1,d1 = self.val
        a2,b2,c2,d2 = o.val
        return Q(
            (a1*a2 - b1*b2 - c1*c2 - d1*d2)%q,
            (a1*b2 + b1*a2 + c1*d2 - d1*c2)%q,
            (a1*c2 - b1*d2 + c1*a2 + d1*b2)%q,
            (a1*d2 + b1*c2 - c1*b2 + d1*a2)%q
        )

def rand_Q(bound):
    return Q(*[random.randint(-bound, bound) for _ in range(4)])

def generate():
    A = [[rand_Q(q//2) for _ in range(n)] for _ in range(m)]
    s = [rand_Q(B) for _ in range(n)]
    e = [rand_Q(B) for _ in range(m)]

    b = []
    for i in range(m):
        res = Q(0,0,0,0)
        for j in range(n):
            res = res + A[i][j] * s[j]
        b.append(res + e[i])
    return A, s, b
