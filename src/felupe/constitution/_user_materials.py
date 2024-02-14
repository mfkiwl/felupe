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

from ..math import identity, ravel, reshape, sym
from ._models_linear_elasticity import lame_converter
from ._user_materials_models import linear_elastic_plastic_isotropic_hardening


class Material:
    r"""A user-defined material definition with given functions for the (first
    Piola-Kirchhoff) stress tensor :math:`\boldsymbol{P}`, optional constraints on
    additional fields (e.g. :math:`p` and :math:`J`), updated state variables
    :math:`\boldsymbol{\zeta}` as well as the according fourth-order elasticity tensor
    :math:`\mathbb{A}` and the linearizations of the constraint equations. Both
    functions take a list of the 3x3 deformation gradient :math:`\boldsymbol{F}` and
    optional vector of state variables :math:`\boldsymbol{\zeta}_n` as the first input
    argument. The stress-function must return the updated state variables
    :math:`\boldsymbol{\zeta}`.
    
    Parameters
    ----------
    stress : callable
        A constitutive material definition which returns a list containting the (first
        Piola-Kirchhoff) stress tensor, optional additional constraints as well as the
        state variables. The state variables must always be included even if they are
        None. See template code-blocks for the required function signature.
    elasticity : callable
        A constitutive material definition which returns a list containing the fourth-
        order elasticity tensor as the jacobian of the (first Piola-Kirchhoff) stress
        tensor w.r.t. the deformation gradient, optional linearizations of the
        additional constraints. The state variables must not be returned. See template
        code-blocks for the required function signature.
    nstatevars : int, optional
        Number of internal state variable components (default is 0). State variable
        components must always be concatenated into a 1d-array.

    Notes
    -----
    
    ..  note::
        The first item in the list of the input arguments always contains the
        gradient of the (displacement) field :math:`\boldsymbol{u}` w.r.t. the
        undeformed coordinates  :math:`\boldsymbol{X}`. The identity matrix
        :math:`\boldsymbol{1}` is added to this gradient, i.e. the first item of the
        list ``x`` contains the deformation gradient :math:`\boldsymbol{F} =
        \boldsymbol{1} + \frac{\partial \boldsymbol{u}}{\partial \boldsymbol{X}}`. All
        other fields are provided as interpolated values (no gradients evaluated).
    
    For :math:`(\boldsymbol{u})` single-field formulations, the callables for
    ``stress`` and ``elasticity`` must return the gradient and hessian of the strain
    energy density function :math:`\psi(\boldsymbol{F})` w.r.t. the deformation
    gradient :math:`\boldsymbol{F}`.
    
    ..  math::

        \text{stress}(\boldsymbol{F}, \boldsymbol{\zeta}_n) &= \begin{bmatrix}
            \frac{\partial \psi}{\partial \boldsymbol{F}} \\
            \boldsymbol{\zeta}
        \end{bmatrix}
        
        \text{elasticity}(\boldsymbol{F}, \boldsymbol{\zeta}_n) &= \begin{bmatrix}
            \frac{\partial^2 \psi}{\partial \boldsymbol{F}\ \partial \boldsymbol{F}}
        \end{bmatrix}
    
    Take this code-block as template:

    ..  code-block::

        def stress(x, **kwargs):
            "First Piola-Kirchhoff stress tensor."

            # extract variables
            F, statevars = x[0], x[-1]

            # user code for (first Piola-Kirchhoff) stress tensor
            P = None

            # update state variables
            statevars_new = None

            return [P, statevars_new]

        def elasticity(x, **kwargs):
            "Fourth-order elasticity tensor."

            # extract variables
            F, statevars = x[0], x[-1]

            # user code for fourth-order elasticity tensor
            # according to the (first Piola-Kirchhoff) stress tensor
            dPdF = None

            return [dPdF]

        umat = Material(stress, elasticity, **kwargs)
        
    For :math:`(\boldsymbol{u}, p, J)` mixed-field formulations, the callables for
    ``stress`` and ``elasticity`` must return the gradients and hessians of the
    (augmented) strain energy density function w.r.t. the deformation gradient and the
    other fields.
    
    ..  math::

        \text{stress}(\boldsymbol{F}, p, J, \boldsymbol{\zeta}_n) &= \begin{bmatrix}
            \frac{\partial \psi}{\partial \boldsymbol{F}} \\
            \frac{\partial \psi}{\partial p} \\
            \frac{\partial \psi}{\partial J} \\
            \boldsymbol{\zeta}
        \end{bmatrix}

    For the hessians, the upper-triangle blocks have to be provided.

    ..  math::

        \text{elasticity}(\boldsymbol{F}, p, J, \boldsymbol{\zeta}_n) &= \begin{bmatrix}
            \frac{\partial^2 \psi}{\partial \boldsymbol{F}\ \partial \boldsymbol{F}} \\
            \frac{\partial^2 \psi}{\partial \boldsymbol{F}\ \partial p} \\
            \frac{\partial^2 \psi}{\partial \boldsymbol{F}\ \partial J} \\
            \frac{\partial^2 \psi}{\partial p\ \partial p} \\
            \frac{\partial^2 \psi}{\partial p\ \partial J} \\
            \frac{\partial^2 \psi}{\partial J\ \partial J}
        \end{bmatrix}

    For :math:`(\boldsymbol{u}, p, J)` mixed-field formulations, take this code-block as
    template:

    ..  code-block::

        def gradient(x, **kwargs):
            "Gradients of the strain energy density function."

            # extract variables
            F, p, J, statevars = x[0], x[1], x[2], x[-1]

            # user code
            dWdF = None  # first Piola-Kirchhoff stress tensor
            dWdp = None
            dWdJ = None

            # update state variables
            statevars_new = None

            return [dWdF, dWdp, dWdJ, statevars_new]

        def hessian(x, **kwargs):
            "Hessians of the strain energy density function."

            # extract variables
            F, p, J, statevars = x[0], x[1], x[2], x[-1]

            # user code
            d2WdFdF = None  # fourth-order elasticity tensor
            d2WdFdp = None
            d2WdFdJ = None
            d2Wdpdp = None
            d2WdpdJ = None
            d2WdJdJ = None

            # upper-triangle items of the hessian
            return [d2WdFdF, d2WdFdp, d2WdFdJ, d2Wdpdp, d2WdpdJ, d2WdJdJ]

        umat = Material(gradient, hessian, **kwargs)

    """

    def __init__(self, stress, elasticity, nstatevars=0, **kwargs):
        self.umat = {"gradient": stress, "hessian": elasticity}
        self.kwargs = kwargs
        self.nstatevars = nstatevars
        self.x = [np.eye(3), np.zeros(nstatevars)]

    def gradient(self, x):
        """Return the evaluated gradient of the strain energy density function.

        Parameters
        ----------
        x : list of ndarray
            The list with input arguments. These contain the extracted fields of a
            :class:`~felupe.FieldContainer` along with the old vector of state
            variables, ``[*[field.extract() for field in fields], statevars_old]``.

        Returns
        -------
        list of ndarray
            A list with the evaluated gradient(s) of the strain energy density function
            and the updated vector of state variables.
        """

        return self.umat["gradient"](x, **self.kwargs)

    def hessian(self, x):
        """Return the evaluated upper-triangle components of the hessian(s) of the
        strain energy density function.

        Parameters
        ----------
        x : list of ndarray
            The list with input arguments. These contain the extracted fields of a
            :class:`~felupe.FieldContainer` along with the old vector of state
            variables, ``[*[field.extract() for field in fields], statevars_old]``.

        Returns
        -------
        list of ndarray
            A list with the evaluated upper-triangle components of the hessian(s) of the
            strain energy density function.
        """

        return self.umat["hessian"](x, **self.kwargs)


class MaterialStrain:
    """A strain-based user-defined material definition with a given function
    for the stress tensor and the (fourth-order) elasticity tensor.

    Take this code-block from the linear-elastic material formulation

    ..  code-block::

        from felupe.math import identity, cdya, dya, trace

        def linear_elastic(dε, εn, σn, ζn, λ, μ, **kwargs):
            '''3D linear-elastic material formulation.

            Arguments
            ---------
            dε : ndarray
                Incremental strain tensor.
            εn : ndarray
                Old strain tensor.
            σn : ndarray
                Old stress tensor.
            ζn : ndarray
                Old state variables.
            λ : float
                First Lamé-constant.
            μ : float
                Second Lamé-constant (shear modulus).
            '''

            # change of stress due to change of strain
            I = identity(dε)
            dσ = 2 * μ * dε + λ * trace(dε) * I

            # update stress and evaluate elasticity tensor
            σ = σn + dσ
            dσdε = 2 * μ * cdya(I, I) + λ * dya(I, I)

            # update state variables (not used here)
            ζ = ζn

            return dσdε, σ, ζ

        umat = MaterialStrain(material=linear_elastic, μ=1, λ=2)

    or this minimal header as template:

    ..  code-block::

        def fun(dε, εn, σn, ζn, **kwargs):
            return dσdε, σ, ζ

        umat = MaterialStrain(material=fun, **kwargs)

    See Also
    --------
    linear_elastic : 3D linear-elastic material formulation
    linear_elastic_plastic_isotropic_hardening : Linear-elastic-plastic material
        formulation with linear isotropic hardening (return mapping algorithm).
    LinearElasticPlasticIsotropicHardening : Linear-elastic-plastic material
        formulation with linear isotropic hardening (return mapping algorithm).

    """

    def __init__(self, material, dim=3, statevars=(0,), **kwargs):
        self.material = material
        self.statevars_shape = statevars
        self.statevars_size = [np.prod(shape) for shape in statevars]
        self.statevars_offsets = np.cumsum(self.statevars_size)
        self.nstatevars = sum(self.statevars_size)

        self.kwargs = {**kwargs, "tangent": None}

        self.dim = dim
        self.x = [np.eye(dim), np.zeros(2 * dim**2 + self.nstatevars)]

        self.stress = self.gradient
        self.elasticity = self.hessian

    def extract(self, x):
        "Extract the input and evaluate strains, stresses and state variables."

        # unpack deformation gradient F = dx/dX
        dim = self.dim
        dxdX, statevars = x

        # small-strain tensor as strain = sym(dx/dX - 1)
        dudx = dxdX - identity(dxdX)
        strain = sym(dudx)

        # separate strain and stress from state variables
        statevars_all = np.split(
            statevars, [*self.statevars_offsets, self.nstatevars + dim**2]
        )
        strain_old_1d, stress_old_1d = statevars_all[-2:]

        # list of state variables with original shapes
        shapes = self.statevars_shape
        statevars_old = [
            reshape(sv, shape).copy() for sv, shape in zip(statevars_all[:-2], shapes)
        ]

        # reshape strain and stress from (dim**2,) to (dim, dim)
        strain_old = strain_old_1d.reshape(dim, dim, *strain_old_1d.shape[1:])
        stress_old = stress_old_1d.reshape(dim, dim, *stress_old_1d.shape[1:])

        # change of strain
        dstrain = strain - strain_old

        return strain_old, dstrain, stress_old, statevars_old

    def gradient(self, x):
        strain_old, dstrain, stress_old, statevars_old = self.extract(x)
        self.kwargs["tangent"] = False

        dsde, stress_new, statevars_new_list = self.material(
            dstrain, strain_old, stress_old, statevars_old, **self.kwargs
        )

        strain_new_1d = (strain_old + dstrain).reshape(-1, *strain_old.shape[2:])
        stress_new_1d = stress_new.reshape(-1, *strain_old.shape[2:])

        statevars_new = np.concatenate(
            [*[ravel(sv) for sv in statevars_new_list], strain_new_1d, stress_new_1d],
            axis=0,
        )

        return [stress_new, statevars_new]

    def hessian(self, x):
        strain_old, dstrain, stress_old, statevars_old = self.extract(x)
        self.kwargs["tangent"] = True

        dsde = self.material(
            dstrain, strain_old, stress_old, statevars_old, **self.kwargs
        )[0]

        # ensure minor-symmetric elasticity tensor due to symmetry of strain
        dsde = (
            dsde
            + np.einsum("ijkl...->jikl...", dsde)
            + np.einsum("ijkl...->ijlk...", dsde)
            + np.einsum("ijkl...->jilk...", dsde)
        ) / 4

        return [dsde]


class LinearElasticPlasticIsotropicHardening(MaterialStrain):
    """Linear-elastic-plastic material formulation with linear isotropic
    hardening (return mapping algorithm).

    Parameters
    ----------
    E : float
        Young's modulus.
    nu : float
        Poisson ratio.
    sy : float
        Initial yield stress.
    K : float
        Isotropic hardening modulus.

    See Also
    --------
    MaterialStrain : A strain-based user-defined material definition with a given
        function for the stress tensor and the (fourth-order) elasticity tensor.
    linear_elastic_plastic_isotropic_hardening : Linear-elastic-plastic material
        formulation with linear isotropic hardening (return mapping algorithm).

    """

    def __init__(self, E, nu, sy, K):
        lmbda, mu = lame_converter(E, nu)

        super().__init__(
            material=linear_elastic_plastic_isotropic_hardening,
            λ=lmbda,
            μ=mu,
            σy=sy,
            K=K,
            dim=3,
            statevars=(1, (3, 3)),
        )
