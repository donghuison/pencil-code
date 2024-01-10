# power.py
#
# Read the power spectra of the simulation.
#
"""
Contains the classes and methods to read the power spectra.
"""

import os
import numpy as np
from pencil import read
from pencil.util import ffloat
import re
import warnings
import functools

def power(*args, **kwargs):
    """
    power(datadir='data', file_name='', quiet=False)

    Read the power spectra.

    Parameters
    ----------
    datadir : string
        Directory where the data is stored.

    file_name : string
        Filename to read.
        If a filename is given, only that power spectrum is read.
        By default it reads all the power spectrum files.

    quiet : bool
        Flag for switching off output.

    Returns
    -------
    Class containing the different power spectrum as attributes.

    Notes
    -----
    Use the attribute keys to get a list of attributes

    Examples
    --------
    >>> pw = pc.read.power()
    >>> pw.keys()
    t
    kin
    krms
    hel_kin
    """

    power_tmp = Power()
    power_tmp.read(*args, **kwargs)
    return power_tmp


class Power(object):
    """
    Power -- holds power spectrum data.
    """

    def __init__(self):
        """
        Fill members with default values.
        """

        self.t = []

    def keys(self):
        for i in self.__dict__.keys():
            print(i)

    def read(self, datadir="data", file_name=None, quiet=False):
        """
        read(datadir='data', file_name='', quiet=False)
    
        Read the power spectra.
    
        Parameters
        ----------
        datadir : string
            Directory where the data is stored.
    
        file_name : string
            Filename to read.
            If a filename is given, only that power spectrum is read.
            By default it reads all the power spectrum files.
    
        quiet : bool
            Flag for switching off output.
    
        Returns
        -------
        Class containing the different power spectrum as attributes.
    
        Notes
        -----
        Use the attribute keys to get a list of attributes
    
        Examples
        --------
        >>> pw = pc.read.power()
        >>> pw.keys()
        t
        kin
        krms
        hel_kin
        """

        power_list = []
        file_list = []

        if file_name is not None:
            if not quiet:
                print("Reading only ", file_name)

            if os.path.isfile(os.path.join(datadir, file_name)):
                if file_name[:5] == "power" and file_name[-4:] == ".dat":
                    if file_name[:6] == "power_":
                        power_list.append(file_name.split(".")[0][6:])
                        if not quiet:
                            print("appending", file_name.split(".")[0][6:])
                    else:
                        power_list.append(file_name.split(".")[0][5:])
                        if not quiet:
                            print("appending", file_name.split(".")[0][5:])

                    file_list.append(file_name)
            else:
                raise ValueError(f"File {file_name} does not exist.")

        else:
            for file_name in os.listdir(datadir):
                if file_name[:5] == "power" and file_name[-4:] == ".dat":
                    if file_name[:6] == "power_":
                        power_list.append(file_name.split(".")[0][6:])
                    else:
                        power_list.append(file_name.split(".")[0][5:])
                    file_list.append(file_name)

        # Read the power spectra.
        for power_name, file_name in zip(power_list, file_list):
            if not quiet:
                print(file_name)

            if (
                file_name == "powero.dat"
                or file_name == "powerb.dat"
                or file_name == "powera.dat"
                ):
                # Exclude some incompatible files.
                pass
            elif re.match("power.*_xy.dat", file_name):
                self._read_power2d(power_name, file_name, datadir)
            elif (
                file_name == "poweruz_x.dat"
                or file_name == "powerux_x.dat"
                or file_name == "poweruy_x.dat"
                ):
                self._read_power_1d(power_name, file_name, datadir)
            elif file_name == "power_krms.dat":
                self._read_power_krms(power_name, file_name, datadir)
            else:
                self._read_power(power_name, file_name, datadir)

    def _read_power2d(self, power_name, file_name, datadir):
        """
        Handles output of power_xy subroutine.
        """
        dim = read.dim(datadir=datadir)
        param = read.param(datadir=datadir)

        with open(os.path.join(datadir, file_name), "r") as f:
            _ = f.readline()  # ignore first line
            header = f.readline()

            # Get k vectors:
            if param.lintegrate_shell:
                nk = int(
                    header
                    .split()[header.split().index("k") + 1]
                    .split(")")[0][1:]
                    )
                k = []
                for _ in range(int(np.ceil(nk / 8))):
                    line = f.readline()
                    k.extend([float(j) for j in line.split()])
                k = np.array(k)
                self.k = k
            else:
                nkx = int(
                    header
                    .split()[header.split().index("k_x") + 1]
                    .split(")")[0][1:]
                    )
                kx = []
                for _ in range(int(np.ceil(nkx / 8))):
                    line = f.readline()
                    kx.extend([float(j) for j in line.split()])
                kx = np.array(kx)
                self.kx = kx

                nky = int(
                    header
                    .split()[header.split().index("k_y") + 1]
                    .split(")")[0][1:]
                    )
                ky = []
                for _ in range(int(np.ceil(nky / 8))):
                    line = f.readline()
                    ky.extend([float(j) for j in line.split()])
                ky = np.array(ky)
                self.ky = ky

                nk = nkx * nky

            # Now read z-positions, if any
            if param.lintegrate_z:
                nzpos = 1
            else:
                ini = f.tell()
                line = f.readline()
                if "z-pos" in line:
                    nzpos = int(re.search(r"\((\d+)\)", line)[1])
                    line = f.readline()
                    # KG: is it never possible for zpos to be broken across more than one line? TODO
                    self.zpos = np.array([float(j) for j in line.split()])
                else:
                    # there was no list of z-positions, so reset the position of the reader.
                    f.seek(ini)

                    nzpos = dim.nzgrid
                    grid = read.grid(datadir=datadir, trim=True, quiet=True)
                    self.zpos = grid.z

            # Now read the rest of the file
            time = []
            power_array = []

            if param.lintegrate_shell:
                block_size = np.ceil(nk / 8) * nzpos + 1
            else:
                block_size = np.ceil(int(nk * nzpos) / 8) + 1

            for line_idx, line in enumerate(f):
                if line_idx % block_size == 0:
                    time.append(float(line.strip()))
                else:
                    lsp = line.strip().split()

                    if len(lsp) == 8:
                        # real power spectrum
                        for value_string in lsp:
                            power_array.append(ffloat(value_string))
                    elif len(lsp) == 16:
                        # complex power spectrum
                        real = lsp[0::2]
                        imag = lsp[1::2]
                        for a, b in zip(real, imag):
                            power_array.append(ffloat(a) + 1j * ffloat(b))
                    else:
                        raise NotImplementedError(f"Unsupported line length ({len(lsp)})")

        time = np.array(time)

        if len(lsp) == 8:
            power_array = np.array(power_array, dtype=np.float32)
        elif len(lsp) == 16:
            power_array = np.array(power_array, dtype=complex)
        else:
            raise NotImplementedError(f"Unsupported line length ({len(lsp)})")

        if param.lintegrate_shell or (dim.nxgrid == 1 or dim.nygrid == 1):
            power_array = power_array.reshape([len(time), nzpos, nk])
        else:
            power_array = power_array.reshape([len(time), nzpos, nky, nkx])

        self.t = time.astype(np.float32)
        self.nzpos = nzpos
        setattr(self, power_name, power_array)

    def _read_power_1d(self, power_name, file_name, datadir):
        """
        Handle output of subroutine power_1d
        """
        dim = read.dim(datadir=datadir)

        block_size = np.ceil(int(dim.nxgrid / 2) / 8.0) + 1

        time = []
        power_array = []
        with open(os.path.join(datadir, file_name), "r") as f:
            for line_idx, line in enumerate(f):
                if np.mod(line_idx, block_size) == 0:
                    time.append(float(line.strip()))
                elif line.find(",") == -1:
                    # if the line does not contain ',', assume it represents a series of real numbers.
                    for value_string in line.strip().split():
                        power_array.append(float(value_string))
                else:
                    # Assume we have complex numbers.
                    for value_string in line.strip().split("( ")[1:]:
                        value_string = (
                            value_string.replace(")", "j")
                            .strip()
                            .replace(", ", "")
                            .replace(" ", "+")
                        )
                        power_array.append(complex(value_string))

        time = np.array(time)
        power_array = np.array(power_array).reshape([len(time), int(dim.nxgrid / 2)])
        self.t = time
        setattr(self, power_name, power_array)

    def _read_power_krms(self, power_name, file_name, datadir):
        """
        Read power_krms.dat.
        """
        nk = self._get_nk_xyz(datadir)
        block_size = np.ceil(nk/8)

        power_array = []
        with open(os.path.join(datadir, file_name), "r") as f:
            for line_idx, line in enumerate(f):
                # KG: Is this file expected to contain extra lines? If not, the if below can be removed.
                if line_idx < block_size:
                    for value_string in line.strip().split():
                        power_array.append(float(value_string))
        power_array = (
            np.array(power_array).reshape([nk]).astype(np.float32)
        )
        setattr(self, power_name, power_array)

    def _read_power(self, power_name, file_name, datadir):
        """
        Handles output of power subroutine.
        """
        nk = self._get_nk_xyz(datadir)
        block_size = np.ceil(nk/8) + 1

        time = []
        power_array = []
        with open(os.path.join(datadir, file_name), "r") as f:
            for line_idx, line in enumerate(f):
                if np.mod(line_idx, block_size) == 0:
                    time.append(float(line.strip()))
                else:
                    for value_string in line.strip().split():
                        power_array.append(ffloat(value_string))

        # Reformat into arrays.
        time = np.array(time)
        power_array = (
            np.array(power_array)
            .reshape([len(time), nk])
            .astype(np.float32)
        )
        self.t = time.astype(np.float32)
        setattr(self, power_name, power_array)

    @functools.lru_cache
    def _get_nk_xyz(self, datadir):
        """
        See variable nk_xyz in power_spectrum.f90.

        NOTE: If you want to read output from non-cubic-box simulations run using older versions of Pencil where the number of k-vectors was always taken as nxgrid/2, you can do
        ```
        >>> class Power_wrong(pc.read.powers.Power):
        ...     def _get_nk_xyz(self, dim, grid):
        ...         return int(dim.nxgrid/2)

        >>> p = Power_wrong.read()
        ```
        """
        dim = read.dim(datadir=datadir)
        try:
            grid = read.grid(datadir=datadir, quiet=True)
        except FileNotFoundError:
            # KG: Handling this case because there is no grid.dat in `tests/input/serial-1/proc0` and we don't want the test to fail. Should we just drop this and add a grid.dat in the test input?
            warnings.warn("grid.dat not found. Assuming the box is cubical.")
            return int(dim.nxgrid/2)

        Lx = grid.Lx
        Ly = grid.Ly
        Lz = grid.Lz

        L_min = min(Lx, Ly, Lz)
        return int(np.round(min( dim.nxgrid*L_min/(2*Lx), dim.nygrid*L_min/(2*Ly), dim.nzgrid*L_min/(2*Lz) )))
