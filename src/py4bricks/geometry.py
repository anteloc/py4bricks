"""geometry.py - Geometry classes.

- Matrix: 3x3 rotation matrix for piece orientation.
- Vector: 3D vector for piece position and displacement.
    * X-axis is horizontal,
    * Y-axis is vertical (positive is up),
    * Z-axis is depth.
- Vector2D: 2D vector for planar positions.
- Axis: XAxis, YAxis, ZAxis for specifying rotation axes.
- AngleUnits: Radians, Degrees for specifying angle units.
- LDU_PER_STUD: 20 LDU per LDraw stud, applies both horizontally and vertically.
- LDU_PER_PLATE: 8 LDU per plate, applies vertically only.
"""

from __future__ import (
    annotations,  # pylint: disable=invalid-name, too-few-public-methods, missing-docstring
)

import copy
import math
from functools import reduce
from numbers import Number
from typing import overload


LDU_PER_STUD = 20     # 1 stud = 20 LDU horizontally
LDU_PER_PLATE = 8     # 1 plate = 8 LDU vertically
LDU_PER_BRICK_HEIGHT = 24 # 1 brick row = 3 plates = 24 LDU
PLATES_PER_BRICK_HEIGHT = 3  # used to convert brick rows ↔ plates

def studs_to_ldu(studs: int) -> float:
    """Convert studs to LDU."""
    return studs * LDU_PER_STUD

def plates_to_ldu(plates: int) -> float:
    """Convert plates to LDU."""
    return plates * LDU_PER_PLATE

def ldu_to_studs(ldu: float) -> int:
    """Convert LDU to studs."""
    return math.ceil(ldu / LDU_PER_STUD)

def ldu_to_plates(ldu: float) -> int:
    """Convert LDU to plates."""
    return math.ceil(ldu / LDU_PER_PLATE)

def studs_to_plates(studs: int) -> int:
    """Convert studs to plates."""
    return math.ceil(studs * LDU_PER_STUD / LDU_PER_PLATE)

def plates_to_studs(plates: int) -> int:
    """Convert plates to studs."""
    return math.ceil(plates * LDU_PER_PLATE / LDU_PER_STUD)

def plates_to_brick_height(plates: int) -> int:
    """Convert plates to brick rows."""
    return math.ceil(plates / PLATES_PER_BRICK_HEIGHT)

def brick_height_to_plates(brick_height: int) -> int:
    """Convert brick rows to plates."""
    return math.ceil(brick_height * PLATES_PER_BRICK_HEIGHT)

def brick_height_to_ldu(brick_height: int) -> float:
    """Convert brick rows to LDU."""
    return brick_height * LDU_PER_BRICK_HEIGHT

class MatrixError(Exception):
    """Exception raised for matrix operation errors."""

    def __init__(self):
        super().__init__("Invalid axis specified.")


class Axis:
    """Base class for axis representations."""


class XAxis(Axis):
    """X-axis representation."""


class YAxis(Axis):
    """Y-axis representation."""


class ZAxis(Axis):
    """Z-axis representation."""


class AngleUnits:
    """Base class for angle unit representations."""


class Radians(AngleUnits):
    """Radian angle units."""


class Degrees(AngleUnits):
    """Degree angle units."""


def _rows_multiplication(r1, r2):
    return [
        [
            r1[0][0] * r2[0][0] + r1[0][1] * r2[1][0] + r1[0][2] * r2[2][0],
            r1[0][0] * r2[0][1] + r1[0][1] * r2[1][1] + r1[0][2] * r2[2][1],
            r1[0][0] * r2[0][2] + r1[0][1] * r2[1][2] + r1[0][2] * r2[2][2],
        ],
        [
            r1[1][0] * r2[0][0] + r1[1][1] * r2[1][0] + r1[1][2] * r2[2][0],
            r1[1][0] * r2[0][1] + r1[1][1] * r2[1][1] + r1[1][2] * r2[2][1],
            r1[1][0] * r2[0][2] + r1[1][1] * r2[1][2] + r1[1][2] * r2[2][2],
        ],
        [
            r1[2][0] * r2[0][0] + r1[2][1] * r2[1][0] + r1[2][2] * r2[2][0],
            r1[2][0] * r2[0][1] + r1[2][1] * r2[1][1] + r1[2][2] * r2[2][1],
            r1[2][0] * r2[0][2] + r1[2][1] * r2[1][2] + r1[2][2] * r2[2][2],
        ],
    ]


class Matrix:
    """a transformation matrix."""

    def __init__(self, rows):
        self.rows = rows

    def __hash__(self) -> int:
        # Flatten the matrix rows into a tuple of tuples for hashing
        return hash(tuple(tuple(row) for row in self.rows))

    def __repr__(self) -> str:
        values = reduce(lambda x, y: x + y, self.rows)
        format_string = "((%f, %f, %f),\n (%f, %f, %f),\n (%f, %f, %f))"
        return format_string % tuple(values)

    @overload
    def __mul__(self, other: Matrix) -> Matrix: ...
    @overload
    def __mul__(self, other: Vector) -> Vector: ...
    def __mul__(self, other: object) -> Matrix | Vector:
        if isinstance(other, Matrix):
            r1 = self.rows
            r2 = other.rows
            return Matrix(_rows_multiplication(r1, r2))
        if isinstance(other, Vector):
            r = self.rows
            x, y, z = other.x, other.y, other.z
            return Vector(
                r[0][0] * x + r[0][1] * y + r[0][2] * z,
                r[1][0] * x + r[1][1] * y + r[1][2] * z,
                r[2][0] * x + r[2][1] * y + r[2][2] * z,
            )
        raise MatrixError

    @overload
    def __rmul__(self, other: Matrix) -> Matrix: ...
    @overload
    def __rmul__(self, other: Vector) -> Vector: ...
    def __rmul__(self, other: object) -> Matrix | Vector:
        if isinstance(other, Matrix):
            r1 = other.rows
            r2 = self.rows
            return Matrix(_rows_multiplication(r1, r2))
        if isinstance(other, Vector):
            r = self.rows
            x, y, z = other.x, other.y, other.z
            return Vector(
                x * r[0][0] + y * r[1][0] + z * r[2][0],
                x * r[0][1] + y * r[1][1] + z * r[2][1],
                x * r[0][2] + y * r[1][2] + z * r[2][2],
            )
        raise MatrixError

    def copy(self) -> Matrix:
        """Make a copy of this matrix."""
        return Matrix(copy.deepcopy(self.rows))

    def rotate(
        self, angle: float, axis: type[Axis], units: type[AngleUnits] = Degrees,
    ) -> Matrix:
        """Rotate the matrix by an angle around an axis."""
        if units == Degrees:
            c = math.cos(angle / 180.0 * math.pi)
            s = math.sin(angle / 180.0 * math.pi)
        else:
            c = math.cos(angle)
            s = math.sin(angle)
        if axis == XAxis:
            rotation = Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])
        elif axis == YAxis:
            rotation = Matrix([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        elif axis == ZAxis:
            rotation = Matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        else:
            raise MatrixError
        return self * rotation  # type: ignore

    def scale(self, sx: float, sy: float, sz: float) -> Matrix:
        """Scale the matrix by a number."""
        return Matrix([[sx, 0, 0], [0, sy, 0], [0, 0, sz]]) * self # type: ignore

    def transpose(self) -> Matrix:
        """Transpose."""
        r = self.rows
        return Matrix(
            [
                [r[0][0], r[1][0], r[2][0]],
                [r[0][1], r[1][1], r[2][1]],
                [r[0][2], r[1][2], r[2][2]],
            ],
        )

    def det(self) -> float:
        """Return determinant of the matrix."""
        r = self.rows
        terms = [
            r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1]),
            r[0][1] * (r[1][2] * r[2][0] - r[1][0] * r[2][2]),
            r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]),
        ]
        return sum(terms)

    def flatten(self) -> tuple[float, ...]:
        """Flatten the matrix."""
        return tuple(reduce(lambda x, y: x + y, self.rows))

    def fix_diagonal(self) -> bool:
        """POV-Ray does not like matrices with zero diagonal elements."""
        corrected = False
        for i in range(3):
            if self.rows[i][i] == 0.0:
                self.rows[i][i] = 0.001
                corrected = True
        return corrected

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return False
        return self.rows == other.rows


def Identity() -> Matrix:  # noqa: N802
    """Return a transformation matrix representing Identity."""
    return Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])


class Vector:
    """a Vector in 3D where x is horizontal, y is positive-up vertical, and z is depth."""

    def __init__(self, x: float, y: float, z: float):
        self.x, self.y, self.z = x, y, z

    @property
    def repr(self) -> str:
        """Return string representation of vector coordinates."""
        return "%f, %f, %f" % (self.x, self.y, self.z)

    def __repr__(self) -> str:
        return "<Vector: (%s)>" % (self.repr)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))

    def __add__(self, other: Vector) -> Vector:
        x = self.x + other.x
        y = self.y + other.y
        z = self.z + other.z
        # Return a new object.
        return Vector(x, y, z)

    __radd__ = __add__

    def __sub__(self, other: Vector) -> Vector:
        x = self.x - other.x
        y = self.y - other.y
        z = self.z - other.z
        # Return a new object.
        return Vector(x, y, z)

    def __rsub__(self, other: Vector) -> Vector:
        x = other.x - self.x
        y = other.y - self.y
        z = other.z - self.z
        # Return a new object.
        return Vector(x, y, z)

    def __cmp__(self, other: Vector) -> bool:
        # This next expression will only return zero (equals) if all
        # expressions are false.
        return self.x != other.x or self.y != other.y or self.z != other.z

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __abs__(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def __rmul__(self, other: float) -> Vector:
        if isinstance(other, Number):
            return Vector(self.x * other, self.y * other, self.z * other)
        raise ValueError("Cannot multiply %s with %s" % (self.__class__, type(other)))

    def __truediv__(self, other: float) -> Vector:
        if isinstance(other, Number):
            return Vector(self.x / other, self.y / other, self.z / other)
        raise ValueError("Cannot divide %s with %s" % (self.__class__, type(other)))

    def copy(self) -> Vector:
        """Copy the vector to a new vectors containing the same values.

        This prevents references to the same object.
        """
        return Vector(self.x, self.y, self.z)

    def cross(self, other: Vector) -> Vector:
        """Cross product."""
        return Vector(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def dot(self, other: Vector) -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def norm(self) -> None:
        """Normalize the vector."""
        _length = abs(self)
        self.x = self.x / _length
        self.y = self.y / _length
        self.z = self.z / _length


class Vector2D:
    """a Vector in 2D."""

    def __init__(self, x: float, y: float):
        self.x, self.y = x, y

    def __repr__(self) -> str:
        return "<Vector2D: (%f, %f) >" % (self.x, self.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __add__(self, other: Vector2D) -> Vector2D:
        x = self.x + other.x
        y = self.y + other.y
        # Return a new object.
        return Vector2D(x, y)

    __radd__ = __add__

    def __sub__(self, other: Vector2D) -> Vector2D:
        x = self.x - other.x
        y = self.y - other.y
        # Return a new object.
        return Vector2D(x, y)

    def __rsub__(self, other: Vector2D) -> Vector2D:
        x = other.x - self.x
        y = other.y - self.y
        # Return a new object.
        return Vector2D(x, y)

    def __cmp__(self, other: Vector2D) -> bool:
        # This next expression will only return zero (equals) if all
        # expressions are false.
        return self.x != other.x or self.y != other.y

    def __abs__(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

    def __rmul__(self, other: float) -> Vector2D:
        if isinstance(other, Number):
            return Vector2D(self.x * other, self.y * other)
        raise ValueError("Cannot multiply %s with %s" % (self.__class__, type(other)))

    def __truediv__(self, other: float) -> Vector2D:
        if isinstance(other, Number):
            return Vector2D(self.x / other, self.y / other)
        raise ValueError("Cannot divide %s with %s" % (self.__class__, type(other)))

    def copy(self) -> Vector2D:
        """Copy the vector to a new vectors containing the same values.

        This prevents references to the same object.
        """
        return Vector2D(self.x, self.y)

    def dot(self, other: Vector2D) -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y


class CoordinateSystem:
    """3D coordinate system representation."""

    def __init__(
        self,
        x: Vector | None = None,
        y: Vector | None = None,
        z: Vector | None = None,
    ):
        self.x = x if x is not None else Vector(1.0, 0.0, 0.0)
        self.y = y if y is not None else Vector(0.0, 1.0, 0.0)
        self.z = z if z is not None else Vector(0.0, 0.0, 1.0)

    def project(self, p: Vector) -> Vector:
        """Project a point onto this coordinate system."""
        return Vector(p.dot(self.x), p.dot(self.y), p.dot(self.z))