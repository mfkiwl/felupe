# -*- coding: utf-8 -*-
"""
This file is part of FElupe.

FElupe is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

FElupe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with FElupe.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np

try:
    from einsumt import einsumt
except ModuleNotFoundError:
    from numpy import einsum as einsumt


def identity(A=None, dim=None, shape=None):
    "Identity according to matrix A with optional specified dim."
    if A is not None:
        dimA = A.shape[0]
        shapeA = A.shape[2:]
        if dim is None:
            dim = dimA
        if shape is None:
            shape = shapeA

    ones = (1,) * len(shape)
    return np.eye(dim).reshape(dim, dim, *ones)


def sym(A, out=None):
    "Symmetric part of matrix A."
    out = np.add(A, transpose(A), out=out)
    return np.multiply(out, 0.5)


def dya(A, B, mode=2, parallel=False, **kwargs):
    "Dyadic (outer or kronecker) product of two tensors."

    if mode == 2:
        return np.multiply(A[:, :, None, None], B[None, None, :, :], **kwargs)
    elif mode == 1:
        return np.multiply(A[:, None], B[None, :], **kwargs)
    else:
        raise ValueError("unknown mode. (1 or 2)", mode)


def inv(A, determinant=None, full_output=False, sym=False, out=None):
    """ "Inverse of A with optionally pre-calculated determinant,
    optional additional output of the calculated determinant or
    a simplified calculation of the inverse for sym. matrices."""

    detAinvA = out
    if detAinvA is None:
        detAinvA = np.zeros_like(A)

    x1 = None
    x2 = None
    if A.shape[:2] == (3, 3):
        # diagonal items
        x1 = np.multiply(A[1, 2], A[2, 1], out=x1)
        x2 = np.multiply(A[1, 1], A[2, 2], out=x2)
        np.add(-x1, x2, out=detAinvA[0, 0])

        x1 = np.multiply(A[0, 2], A[2, 0], out=x1)
        x2 = np.multiply(A[0, 0], A[2, 2], out=x2)
        np.add(-x1, x2, out=detAinvA[1, 1])

        x1 = np.multiply(A[0, 1], A[1, 0], out=x1)
        x2 = np.multiply(A[0, 0], A[1, 1], out=x2)
        np.add(-x1, x2, out=detAinvA[2, 2])

        # upper-triangle off-diagonal
        x1 = np.multiply(A[0, 1], A[2, 2], out=x1)
        x2 = np.multiply(A[0, 2], A[2, 1], out=x2)
        np.add(-x1, x2, out=detAinvA[0, 1])

        x1 = np.multiply(A[0, 2], A[1, 1], out=x1)
        x2 = np.multiply(A[0, 1], A[1, 2], out=x2)
        np.add(-x1, x2, out=detAinvA[0, 2])

        x1 = np.multiply(A[0, 0], A[1, 2], out=x1)
        x2 = np.multiply(A[0, 2], A[1, 0], out=x2)
        np.add(-x1, x2, out=detAinvA[1, 2])

        if sym:
            detAinvA[1, 0] = detAinvA[0, 1]
            detAinvA[2, 0] = detAinvA[0, 2]
            detAinvA[2, 1] = detAinvA[1, 2]
        else:
            # lower-triangle off-diagonal
            x1 = np.multiply(A[1, 0], A[2, 2], out=x1)
            x2 = np.multiply(A[2, 0], A[1, 2], out=x2)
            np.add(-x1, x2, out=detAinvA[1, 0])

            x1 = np.multiply(A[2, 0], A[1, 1], out=x1)
            x2 = np.multiply(A[1, 0], A[2, 1], out=x2)
            np.add(-x1, x2, out=detAinvA[2, 0])

            x1 = np.multiply(A[0, 0], A[2, 1], out=x1)
            x2 = np.multiply(A[2, 0], A[0, 1], out=x2)
            np.add(-x1, x2, out=detAinvA[2, 1])

    elif A.shape[:2] == (2, 2):
        detAinvA[0, 0] = A[1, 1]
        detAinvA[0, 1] = -A[0, 1]
        detAinvA[1, 0] = -A[1, 0]
        detAinvA[1, 1] = A[0, 0]

    elif A.shape[:2] == (1, 1):
        detAinvA[0, 0] = 1

    else:
        raise ValueError(
            " ".join(
                [
                    "Wrong shape of first two axes.",
                    "Must be (1, 1), (2, 2) or (3, 3) but {A.shape[:2]} is given.",
                ]
            )
        )

    if determinant is None:
        detA = det(A, out=x1)
    else:
        detA = determinant

    if full_output:
        return np.divide(detAinvA, detA, out=detAinvA), detA
    else:
        return np.divide(detAinvA, detA, out=detAinvA)


def det(A, out=None):
    "Return the determinant of symmetric matrices A."

    detA = out
    if detA is None:
        detA = np.zeros_like(A[0, 0])
    else:
        detA.fill(0)

    if A.shape[:2] == (3, 3):
        tmp = np.multiply(A[0, 0], A[1, 1])
        np.multiply(tmp, A[2, 2], out=tmp)
        np.add(detA, tmp, out=detA)

        tmp = np.multiply(A[0, 1], A[1, 2], out=tmp)
        np.multiply(tmp, A[2, 0], out=tmp)
        np.add(detA, tmp, out=detA)

        tmp = np.multiply(A[0, 2], A[1, 0], out=tmp)
        np.multiply(tmp, A[2, 1], out=tmp)
        np.add(detA, tmp, out=detA)

        tmp = np.multiply(A[2, 0], A[1, 1], out=tmp)
        np.multiply(tmp, A[0, 2], out=tmp)
        np.add(detA, -tmp, out=detA)

        tmp = np.multiply(A[2, 1], A[1, 2], out=tmp)
        np.multiply(tmp, A[0, 0], out=tmp)
        np.add(detA, -tmp, out=detA)

        tmp = np.multiply(A[2, 2], A[1, 0], out=tmp)
        np.multiply(tmp, A[0, 1], out=tmp)
        np.add(detA, -tmp, out=detA)

    elif A.shape[:2] == (2, 2):
        tmp = np.multiply(A[0, 0], A[1, 1])
        np.add(detA, tmp, out=detA)

        tmp = np.multiply(A[1, 0], A[0, 1], out=tmp)
        np.add(detA, -tmp, out=detA)

    elif A.shape[:2] == (1, 1):
        np.add(detA, A[0, 0], out=detA)

    else:
        raise ValueError(
            " ".join(
                [
                    "Wrong shape of first two axes.",
                    "Must be (1, 1), (2, 2) or (3, 3) but {A.shape[:2]} is given.",
                ]
            )
        )
    return detA


def dev(A):
    "Deviator of matrix A."
    dim = A.shape[0]
    return A - trace(A) / dim * identity(A)


def cof(A):
    "Cofactor matrix of A (as a wrapper for the inverse of A)."
    return transpose(inv(A, determinant=1.0))


def eig(A, eig=np.linalg.eig):
    "Eigenvalues and -vectors of matrix A."
    wA, vA = eig(A.T)
    return wA.T, vA.T


def eigh(A):
    "Eigenvalues and -vectors of a symmetric matrix A."
    return eig(A, eig=np.linalg.eigh)


def eigvals(A, shear=False, eig=np.linalg.eig):
    "Eigenvalues (and optional principal shear values) of a matrix A."
    wA = eig(A.T)[0].T
    if shear:
        dim = wA.shape[0]
        if dim == 3:
            ij = [(1, 0), (2, 0), (2, 1)]
        elif dim == 2:
            ij = [(1, 0)]
        dwA = np.array([wA[i] - wA[j] for i, j in ij])
        return np.vstack((wA, dwA))
    else:
        return wA


def eigvalsh(A, shear=False):
    "Eigenvalues (and optional principal shear values) of a symmetric matrix A."
    return eigvals(A, shear=shear, eig=np.linalg.eigh)


def transpose(A, mode=1):
    "Transpose (mode=1) or major-transpose (mode=2) of matrix A."
    if mode == 1:
        return np.einsum("ij...->ji...", A)
    elif mode == 2:
        return np.einsum("ijkl...->klij...", A)
    else:
        raise ValueError("Unknown value of mode.")


def majortranspose(A):
    return transpose(A, mode=2)


def trace(A):
    "The sum of the diagonal elements of A."
    return np.trace(A)


def cdya_ik(A, B, parallel=False, **kwargs):
    "ik - crossed dyadic-product of A and B."
    if parallel:
        einsum = einsumt
    else:
        einsum = np.einsum
    return einsum("ij...,kl...->ikjl...", A, B, **kwargs)


def cdya_il(A, B, parallel=False, **kwargs):
    "il - crossed dyadic-product of A and B."
    if parallel:
        einsum = einsumt
    else:
        einsum = np.einsum
    return einsum("ij...,kl...->ilkj...", A, B, **kwargs)


def cdya(A, B, parallel=False, out=None, **kwargs):
    "symmetric - crossed dyadic-product of A and B."
    res = cdya_ik(A, B, parallel=parallel, out=out, **kwargs)
    res = np.add(res, cdya_il(A, B, parallel=parallel, **kwargs), out=res)
    return np.multiply(res, 0.5, out=res)


def cross(a, b):
    "Cross product of two vectors a and b."
    return np.einsum(
        "...i->i...", np.cross(np.einsum("i...->...i", a), np.einsum("i...->...i", b))
    )


def dot(A, B, mode=(2, 2), parallel=False, **kwargs):
    "Dot-product of A and B with inputs of n trailing axes.."

    if parallel:
        einsum = einsumt
    else:
        einsum = np.einsum

    if mode == (2, 2):
        return einsum("ik...,kj...->ij...", A, B, **kwargs)
    elif mode == (1, 1):
        return einsum("i...,i...->...", A, B, **kwargs)
    elif mode == (4, 4):
        return einsum("ijkp...,plmn...->ijklmn...", A, B, **kwargs)
    elif mode == (2, 1):
        return einsum("ij...,j...->i...", A, B, **kwargs)
    elif mode == (1, 2):
        return einsum("i...,ij...->j...", A, B, **kwargs)
    elif mode == (2, 3):
        return einsum("im...,mjk...->ijk...", A, B, **kwargs)
    elif mode == (3, 2):
        return einsum("ijm...,mk...->ijk...", A, B, **kwargs)
    elif mode == (4, 1):
        return einsum("ijkl...,l...->ijk...", A, B, **kwargs)
    elif mode == (1, 4):
        return einsum("i...,ijkl...->jkl...", A, B, **kwargs)
    elif mode == (2, 4):
        return einsum("im...,mjkl...->ijkl...", A, B, **kwargs)
    elif mode == (4, 2):
        return einsum("ijkm...,ml...->ijkl...", A, B, **kwargs)
    else:
        raise TypeError("Unknown shape of A and B.")


def ddot(A, B, mode=(2, 2), parallel=False, **kwargs):
    "Double-Dot-product of A and B with inputs of `n` trailing axes."

    if parallel:
        einsum = einsumt
    else:
        einsum = np.einsum

    if mode == (2, 2):
        return einsum("ij...,ij...->...", A, B, **kwargs)
    elif mode == (2, 4):
        return einsum("ij...,ijkl...->kl...", A, B, **kwargs)
    elif mode == (4, 2):
        return einsum("ijkl...,kl...->ij...", A, B, **kwargs)
    elif mode == (2, 3):
        return einsum("ij...,ijk...->k...", A, B, **kwargs)
    elif mode == (3, 2):
        return einsum("ijk...,jk...->i...", A, B, **kwargs)
    elif mode == (4, 4):
        return einsum("ijkl...,klmn...->ijmn...", A, B, **kwargs)
    else:
        raise TypeError("Unknown shape of A and B.")


def tovoigt(A, strain=False):
    "Convert (3, 3) tensor to (6, ) voigt notation."
    dim = A.shape[0]
    if dim == 2:
        B = np.zeros((3, *A.shape[2:]))
        ij = [(0, 0), (1, 1), (0, 1)]
    else:
        B = np.zeros((6, *A.shape[2:]))
        ij = [(0, 0), (1, 1), (2, 2), (0, 1), (1, 2), (0, 2)]
    for i6, (i, j) in enumerate(ij):
        B[i6] = A[i, j]
    if strain:
        B[dim:] *= 2
    return B


def reshape(A, shape, trailing_axes=2):
    return A.reshape(np.append(shape, A.shape[-trailing_axes:]))


def ravel(A, trailing_axes=2):
    ij, shape = np.split(A.shape, [-trailing_axes])
    return reshape(A, shape=np.prod(ij))


def equivalent_von_mises(A):
    r"""Return the Equivalent von Mises values of square matrices.

    ..  math::

        \boldsymbol{A}_{v} = \sqrt{
            \frac{3}{2} \text{dev}(\boldsymbol{A}) : \text{dev}(\boldsymbol{A})
        }

    Parameters
    ----------
    A : (M, M, ...) ndarray
        Symmetric matrices for which the equivalent von Mises value will be computed.

    Returns
    -------
    AvM : (...) ndarray
        The equivalent von Mises values.
    """

    if A.shape[:2] == (3, 3):
        pass

    elif A.shape[:2] == (2, 2):
        zeros = len(A.shape[2:]) * [(0, 0)]
        A = np.pad(A, ((0, 1), (0, 1), *zeros))

    else:
        raise TypeError(
            "Square matrices must be two- or three-dimensional on the first two axes."
        )

    devA = dev(A)
    return np.sqrt(3 / 2 * ddot(devA, devA))
