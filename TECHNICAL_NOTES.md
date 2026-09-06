# Technical notes

## Pipeline inclination input

The surface pipeline model computes a local elevation slope `dz/dx`.
The hydraulic function expects `sin(theta)`. The implementation therefore
converts the local slope using:

`sin(theta) = slope / sqrt(1 + slope^2)`

This keeps the trigonometric input physically bounded between -1 and 1.
