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
from functools import wraps

from jax.numpy import trace
from jax.numpy.linalg import det

from ....tensortrax.models.hyperelastic import neo_hooke as neo_hooke_docstring


@wraps(neo_hooke_docstring)
def neo_hooke(C, mu):
    return mu / 2 * (det(C) ** (-1 / 3) * trace(C) - 3)
