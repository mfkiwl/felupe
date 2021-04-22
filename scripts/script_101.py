# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 08:45:35 2021

@author: adutz
"""

import numpy as np

from mesh import Cube
from element import Hex1
from domain import Domain
import quadrature
import doftools
from doftools import Boundary
import solve
import constitution

from helpers import identity, dya, det, cof, transpose, dot, eigvals

tol = 1e-5

move = -0.1

mu = 1.0
bulk = 5000.0 * mu
cargs = [mu, bulk]

e = Hex1()
m = Cube(a=(0, 0, 0), b=(2, 2, 1), n=(10, 10, 5))
# m.nodes[:,:2] = 0.8*m.nodes[:,:2] + 0.2*m.nodes[:,:2] * (m.nodes[:,2]**7).reshape(-1,1)
q = quadrature.Linear(dim=3)
c = constitution.NeoHooke()

d = Domain(e, m, q)

# undeformed element volumes
V = d.volume()

# u at nodes
u = d.zeros()
p = np.zeros(d.nelements)
J = np.ones(d.nelements)

# boundaries
f0 = lambda x: np.isclose(x, 0)
f1 = lambda x: np.isclose(x, 1)

symx = Boundary(d.dof, m, "sym-x", skip=(0, 1, 1), fx=f0)
symy = Boundary(d.dof, m, "sym-y", skip=(1, 0, 1), fy=f0)
symz = Boundary(d.dof, m, "sym-z", skip=(1, 1, 0), fz=f0)
movz = Boundary(d.dof, m, "move", skip=(1, 1, 0), fz=f1, value=move)
bounds = [symx, symy, symz, movz]

# symx = Boundary(d.dof, m, "sym-x", skip=(0, 1, 1), fx=f0)
# symy = Boundary(d.dof, m, "sym-y", skip=(1, 0, 1), fy=f0)
# fixb = Boundary(d.dof, m, "sym-z", skip=(1, 1, 0), fz=f0)
# fixt = Boundary(d.dof, m, "fix-t", skip=(0, 0, 1), fz=f1)
# movt = Boundary(d.dof, m, "mov-t", skip=(1, 1, 0), fz=f1, value = move)
# bounds = [symx, symy, fixb, fixt, movt]

# dofs to "D"ismiss and to "I"ntegrate
D, I = doftools.partition(d.dof, bounds)

# obtain external displacements for prescribed dofs
uDext = doftools.apply(u, d.dof, bounds, D)

n_ = []

for iteration in range(100):
    # deformation gradient at integration points
    F = identity(d.grad(u)) + d.grad(u)

    # deformed element volumes
    v = d.volume(det(F))

    # p, J quantities
    dUdJ = bulk * (J - 1)
    d2UdJ2 = bulk

    # additional integral over shape function
    H = d.integrate(cof(F)) / V

    # residuals and tangent matrix
    r1 = d.asmatrix(d.integrate(c.P(F, p, J, *cargs)))
    r2 = d.asmatrix((v / V - J) * V * H)  # * d2UdJ2)
    r3 = d.asmatrix((dUdJ - p) * V * H)

    r = r1 + r2 + r3
    K = d.asmatrix(d.integrate(c.A(F, p, J, *cargs)) + d2UdJ2 * V * dya(H, H))

    system = solve.partition(u, r, K, I, D)
    du = solve.solve(*system, uDext)
    dJ = np.einsum("aie,eai->e", H, du[m.connectivity])
    dp = dJ * d2UdJ2

    if np.any(np.isnan(du)):
        break
    else:
        rref = np.linalg.norm(r[D].toarray()[:, 0])
        if rref == 0:
            norm_r = 1
        else:
            norm_r = np.linalg.norm(r[I].toarray()[:, 0]) / rref
        norm_du = np.linalg.norm(du)
        norm_dp = np.linalg.norm(dp)
        norm_dJ = np.linalg.norm(dJ)
        n_.append(norm_r * rref)
        print(
            f"#{iteration+1:2d}: |f|={norm_r:1.3e} (|δu|={norm_du:1.3e} |δp|={norm_dp:1.3e} |δJ|={norm_dJ:1.3e})"
        )

    u += du
    J += dJ
    p += dp

    if norm_r < tol:
        break

# cauchy stress at integration points
F = identity(d.grad(u)) + d.grad(u)
# v = d.volume(det(F))
# J = v/V
# p = bulk * (J - 1)

# cauchy stress at integration points
s = dot(c.P(F, p, J, *cargs), transpose(F)) / det(F)
sp = eigvals(s)

# shift stresses to nodes and average nodal values
cauchy = d.tonodes(s, sym=True)
cauchyprinc = [d.tonodes(sp_i, mode="scalar") for sp_i in sp]


import meshio

cells = {"hexahedron": m.connectivity}
mesh = meshio.Mesh(
    m.nodes,
    cells,
    # Optionally provide extra data on points, cells, etc.
    point_data={
        "Displacements": u,
        "CauchyStress": cauchy,
        "ReactionForce": r.todense().reshape(*m.nodes.shape),
        "MaxPrincipalCauchyStress": cauchyprinc[2],
        "IntPrincipalCauchyStress": cauchyprinc[1],
        "MinPrincipalCauchyStress": cauchyprinc[0],
    },
    # Each item in cell data must match the cells array
    cell_data={
        "Pressure": [
            p,
        ],
        "Volume-Ratio": [
            J,
        ],
    },
)
mesh.write("out.vtk")

# FZ_move = np.sum(r[movt.dof])
import matplotlib.pyplot as plt

plt.semilogy(n_[1:], "o")
plt.semilogy(np.logspace(-1, -10, 10))
