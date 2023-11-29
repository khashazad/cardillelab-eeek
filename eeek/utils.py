"""
Defines standard functions for x, P, F, Q, H, and R.
"""
import math

import ee


def identity(num_params):
    """Creates an array image of the identity matrix with size num_params.

    Useful for F.

    Args:
        num_params: int

    Returns:
        function: dict -> ee.Image
    """

    def inner(**kwargs):
        return ee.Image(ee.Array.identity(num_params))

    return inner


def constant_diagonal(constant):
    """Creates an array image with constant along the diagonal.

    Useful for Q and P.

    Args:
        constant: list[number]

    Returns:
        function: dict -> ee.Image
    """

    def inner(**kwargs):
        return ee.Image(ee.Array([constant]).transpose().matrixToDiag())

    return inner


def constant_transposed(constant):
    """Creates an array image out of constant with shape (len(constant), 1)

    Useful for x and R.

    Args:
        constant: list[number]

    Returns:
        function: dict -> ee.Image
    """

    def inner(**kwargs):
        return ee.Image(ee.Array([constant]).transpose())

    return inner


def from_band_transposed(band_name, n):
    """Creates an array image with curr[band_name] stacked n times

    Useful to get R from a band e.g. cloud score plus.

    Args:
        band_name: str, band in curr to populate array with
        n: int, shape of resulting array will be (n, 1)

    Returns:
        function: ee.Image, dict -> ee.Image
    """

    def inner(curr, **kwargs):
        return curr.select(band_name).toArray().arrayRepeat(1, n).matrixTranspose()

    return inner


def from_band_diagonal(curr, band_name, n):
    """Creates an array image with curr[band_name] repeated along the diagonal.

    Args:
        band_name: str, band in curr to populate array with
        n: int, shape of resulting array will be (n, n)

    Returns:
        function: ee.Image, dict -> ee.Image
    """

    def inner(curr, **kwargs):
        return (
            curr.select(band_name)
            .toArray()
            .arrayRepeat(1, n)
            .matrixTranspose()
            .matrixToDiag()
        )

    return inner


def sinusoidal(num_params):
    """Creates sinusoid function of the form a + b*cos(2pi*t) + c*sin(2pi*t)...

    Function will have an intercept but no linear term. cos is always paired
    with sin.

    Useful for H.

    Args:
        num_params: int, number of coefficients in the sinusoid function.

    Returns:
        function: ee.Image, dict -> ee.Image
    """

    def inner(t, **kwargs):
        bands = [ee.Image.constant(1.0)]
        for _ in range((num_params - 1) // 2):
            bands.extend([t.multiply(2 * math.pi).cos(), t.multiply(2 * math.pi).sin()])
        image = ee.Image.cat(*bands).toArray(0)
        return image.arrayReshape(ee.Image(ee.Array([1, -1])), 2)

    return inner


def track_updated_measurement(x, H, **kwargs):
    """After updating the state recompute the measurement.

    Can be used as the postprocessing function.

    Args:
        x: ee.Image, the updated state
        H: function: dict -> ee.Image, the measurement function

    Returns:
        ee.Image
    """
    return H(**kwargs).matrixMultiply(x)