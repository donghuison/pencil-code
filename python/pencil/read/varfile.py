# varfile.py
#
# Read the var files.
# NB: the f array returned is C-ordered: f[nvar, nz, ny, nx]
#     NOT Fortran as in Pencil (& IDL):  f[nx, ny, nz, nvar]
#
# Authors:
# J. Oishi (joishi@amnh.org)
# T. Gastine (tgastine@ast.obs-mip.fr)
# S. Candelaresi (iomsn1@gmail.com).
# 20.10.30 IL modified: added comments in the definition
"""
Contains the read class for the VAR file reading,
some simulation attributes and the data cube.
"""
import numpy as np
import warnings
from pencil.math import natural_sort

def var(*args, **kwargs):
    """
    var(var_file='', datadir='data', proc=-1, ivar=-1, quiet=True,
        trimall=False, magic=None, sim=None, precision='f')

    Read VAR files from Pencil Code. If proc < 0, then load all data
    and assemble, otherwise load VAR file from specified processor.

    The file format written by output() (and used, e.g. in var.dat)
    consists of the followinig Fortran records:
    1. data(mx, my, mz, nvar)
    2. t(1), x(mx), y(my), z(mz), dx(1), dy(1), dz(1), deltay(1)
    Here nvar denotes the number of slots, i.e. 1 for one scalar field, 3
    for one vector field, 8 for var.dat in the case of MHD with entropy.
    but, deltay(1) is only there if lshear is on! need to know parameters.


    Parameters
    ----------
     var_file : string
         Name of the VAR file.
         If not specified, use var.dat (which is the latest snapshot of the fields)

     datadir : string
         Directory where the data is stored.

     proc : int
         Processor to be read. If -1 read all and assemble to one array.

     ivar : int
       Index of the VAR file, if var_file is not specified.

     quiet : bool
         Flag for switching off output.

     trimall : bool
         Trim the data cube to exclude ghost zones.

     magic : bool
         Values to be computed from the data, e.g. B = curl(A).

     sim : pencil code simulation object
         Contains information about the local simulation.

     precision : string
         Float 'f', double 'd' or half 'half'.

     lpersist : bool
         Read the persistent variables if they exist

    Returns
    -------
    DataCube
        Instance of the pencil.read.var.DataCube class.
        All of the computed fields are imported as class members.

    Examples
    --------
    Read the latest var.dat file and print the shape of the uu array:
    >>> var = pc.read.var()
    >>> print(var.uu.shape)

    Read the VAR2 file, compute the magnetic field B = curl(A),
    the vorticity omega = curl(u) and remove the ghost zones:
    >>> var = pc.read.var(var_file='VAR2', magic=['bb', 'vort'], trimall=True)
    >>> print(var.bb.shape)
    """

    from pencil.sim import __Simulation__

    started = None

    for a in args:
        if isinstance(a, __Simulation__):
            started = a.started()
            break

    if "sim" in kwargs.keys():
        # started = kwargs['sim'].started()

        started = True
    elif "datadir" in kwargs.keys():
        from os.path import join, exists

        if exists(join(kwargs["datadir"], "time_series.dat")):
            started = True
    else:
        from os.path import join, exists

        if exists(join("data", "time_series.dat")):
            started = True

    if not started:
        if "ivar" in kwargs:
            if kwargs["ivar"] != 0:
                print("ERROR: Simulation has not yet started. There are no var files.")
                return False

    var_tmp = DataCube()
    var_tmp.read(*args, **kwargs)
    return var_tmp


class DataCube(object):
    """
    DataCube -- holds Pencil Code VAR file data.
    """

    def __init__(self):
        """
        Fill members with default values.
        """

        self.t = 0.0
        self.dx = 1.0
        self.dy = 1.0
        self.dz = 1.0
        self.x = None
        self.y = None
        self.z = None
        self.f = None
        self.l1 = None
        self.l2 = None
        self.m1 = None
        self.m2 = None
        self.n1 = None
        self.n2 = None
        self.magic = None

    def keys(self):
        for i in self.__dict__.keys():
            print(i)

    def read(
        self,
        var_file="",
        datadir="data",
        proc=-1,
        ivar=-1,
        quiet=True,
        trimall=False,
        magic=None,
        sim=None,
        precision="d",
        lpersist=False,
        dtype=np.float64,
    ):
        """
        read(var_file='', datadir='data', proc=-1, ivar=-1, quiet=True,
             trimall=False, magic=None, sim=None, precision='d')

        Read VAR files from Pencil Code. If proc < 0, then load all data
        and assemble, otherwise load VAR file from specified processor.

        The file format written by output() (and used, e.g. in var.dat)
        consists of the followinig Fortran records:
        1. data(mx, my, mz, nvar)
        2. t(1), x(mx), y(my), z(mz), dx(1), dy(1), dz(1), deltay(1)
        Here nvar denotes the number of slots, i.e. 1 for one scalar field, 3
        for one vector field, 8 for var.dat in the case of MHD with entropy.
        but, deltay(1) is only there if lshear is on! need to know parameters.


        Parameters
        ----------
         var_file : string
             Name of the VAR file.
             If not specified, use var.dat (which is the latest snapshot of the fields)

         datadir : string
             Directory where the data is stored.

         proc : int
             Processor to be read. If -1 read all and assemble to one array.

         ivar : int
           Index of the VAR file, if var_file is not specified.

         quiet : bool
             Flag for switching off output.

         trimall : bool
             Trim the data cube to exclude ghost zones.

         magic : bool
             Values to be computed from the data, e.g. B = curl(A).

         sim : pencil code simulation object
             Contains information about the local simulation.

         precision : string
             Float 'f', double 'd' or half 'half'.

         lpersist : bool
             Read the persistent variables if they exist

        Returns
        -------
        DataCube
            Instance of the pencil.read.var.DataCube class.
            All of the computed fields are imported as class members.

        Examples
        --------
        Read the latest var.dat file and print the shape of the uu array:
        >>> var = pc.read.var()
        >>> print(var.uu.shape)

        Read the VAR2 file, compute the magnetic field B = curl(A),
        the vorticity omega = curl(u) and remove the ghost zones:
        >>> var = pc.read.var(var_file='VAR2', magic=['bb', 'vort'], trimall=True)
        >>> print(var.bb.shape)
        """

        import os
        from scipy.io import FortranFile
        from pencil.math.derivatives import curl, curl2
        from pencil import read

        def persist(self, infile=None, precision="d", quiet=quiet):
            """An open Fortran file potentially containing persistent variables appended
            to the f array and grid data are read from the first proc data

            Record types provide the labels and id record for the peristent
            variables in the depricated fortran binary format
            """
            record_types = {}
            for key in read.record_types.keys():
                if read.record_types[key][1] == "d":
                    record_types[key] = (read.record_types[key][0], precision)
                else:
                    record_types[key] = read.record_types[key]

            try:
                tmp_id = infile.read_record("h")
            except:
                return -1
            block_id = 0
            for i in range(2000):
                i += 1
                tmp_id = infile.read_record("h")
                block_id = tmp_id[0]
                if block_id == 2000:
                    break
                for key in record_types.keys():
                    if record_types[key][0] == block_id:
                        tmp_val = infile.read_record(record_types[key][1])
                        self.__setattr__(key, tmp_val[0])
                        if not quiet:
                            print(
                                key, record_types[key][0], record_types[key][1], tmp_val
                            )
            return self

        if sim is None:
            datadir = os.path.expanduser(datadir)

            if var_file[0:2].lower() == "og":
                dim = read.ogdim(datadir, proc)
            else:
                if var_file[0:4] == "VARd":
                    dim = read.dim(datadir, proc, down=True)
                else:
                    dim = read.dim(datadir, proc)

            param = read.param(datadir=datadir, quiet=quiet, conflicts_quiet=True)

            index = read.index(datadir=datadir)

            try:
                grid = read.grid(datadir=datadir, quiet=True)
            except FileNotFoundError:
                # KG: Handling this case because there is no grid.dat in `tests/input/serial-1/proc0` and we don't want the test to fail. Should we just drop this and add a grid.dat in the test input?
                warnings.warn("Grid.dat not found. Assuming the grid is uniform.")
        else:
            datadir = os.path.expanduser(sim.datadir)
            dim = sim.dim
            param = read.param(datadir=sim.datadir, quiet=True, conflicts_quiet=True)
            index = read.index(datadir=sim.datadir)
            grid = read.grid(datadir=sim.datadir, quiet=True)

        if param.lwrite_aux:
            total_vars = dim.mvar + dim.maux
        else:
            total_vars = dim.mvar

        lh5 = False
        if hasattr(param, "io_strategy") and param.io_strategy == "HDF5":
            lh5 = True
        # Keep this for sims that were converted from Fortran to hdf5
        if os.path.exists(os.path.join(datadir, "grid.h5")):
            lh5 = True
        if lh5:
            #
            #  Read HDF5 files.
            #
            import h5py

            run2D = param.lwrite_2d

            # Set up the global array.
            if not run2D:
                self.f = np.zeros((total_vars, dim.mz, dim.my, dim.mx), dtype=dtype)
            else:
                if dim.ny == 1:
                    self.f = np.zeros((total_vars, dim.mz, dim.mx), dtype=dtype)
                else:
                    self.f = np.zeros((total_vars, dim.my, dim.mx), dtype=dtype)

            if not var_file:
                if ivar < 0:
                    var_file = "var.h5"
                else:
                    var_file = "VAR" + str(ivar) + ".h5"

            file_name = os.path.join(datadir, "allprocs", var_file)
            with h5py.File(file_name, "r") as tmp:
                for key in tmp["data"].keys():
                    self.f[index.__getattribute__(key) - 1, :] = dtype(
                        tmp["data/" + key][:]
                    )
                t = (tmp["time"][()]).astype(precision)
                x = (tmp["grid/x"][()]).astype(precision)
                y = (tmp["grid/y"][()]).astype(precision)
                z = (tmp["grid/z"][()]).astype(precision)
                dx = (tmp["grid/dx"][()]).astype(precision)
                dy = (tmp["grid/dy"][()]).astype(precision)
                dz = (tmp["grid/dz"][()]).astype(precision)
                if param.lshear:
                    deltay = (tmp["persist/shear_delta_y"][(0)]).astype(precision)
                if lpersist:
                    for key in tmp["persist"].keys():
                        self.__setattr__(
                            key, (tmp["persist"][key][0]).astype(precision)
                        )
        elif (hasattr(param, "io_strategy") and param.io_strategy == "dist"
             ) or not hasattr(param, "io_strategy"):
            #
            #  Read scattered Fortran binary files.
            #
            run2D = param.lwrite_2d

            if dim.precision == "D":
                read_precision = "d"
            else:
                read_precision = "f"

            if not var_file:
                if ivar < 0:
                    var_file = "var.dat"
                else:
                    var_file = "VAR" + str(ivar)

            if proc < 0:
                proc_dirs = self.__natural_sort(
                    filter(lambda s: s.startswith("proc"), os.listdir(datadir))
                )
                if proc_dirs.count("proc_bounds.dat") > 0:
                    proc_dirs.remove("proc_bounds.dat")
                if param.lcollective_io:
                    # A collective IO strategy is being used
                    proc_dirs = ["allprocs"]
            #                else:
            #                    proc_dirs = proc_dirs[::dim.nprocx*dim.nprocy]
            else:
                proc_dirs = ["proc" + str(proc)]

            # Set up the global array.
            if not run2D:
                self.f = np.zeros((total_vars, dim.mz, dim.my, dim.mx), dtype=dtype)
            else:
                if dim.ny == 1:
                    self.f = np.zeros((total_vars, dim.mz, dim.mx), dtype=dtype)
                else:
                    self.f = np.zeros((total_vars, dim.my, dim.mx), dtype=dtype)

            x = np.zeros(dim.mx, dtype=precision)
            y = np.zeros(dim.my, dtype=precision)
            z = np.zeros(dim.mz, dtype=precision)

            for directory in proc_dirs:
                if not param.lcollective_io:
                    proc = int(directory[4:])
                    if var_file[0:2].lower() == "og":
                        procdim = read.ogdim(datadir, proc)
                    else:
                        if var_file[0:4] == "VARd":
                            procdim = read.dim(datadir, proc, down=True)
                        else:
                            procdim = read.dim(datadir, proc)
                    if not quiet:
                        print(
                            "Reading data from processor"
                            + " {0} of {1} ...".format(proc, len(proc_dirs))
                        )

                else:
                    # A collective IO strategy is being used
                    procdim = dim
                #                else:
                #                    procdim.mx = dim.mx
                #                    procdim.my = dim.my
                #                    procdim.nx = dim.nx
                #                    procdim.ny = dim.ny
                #                    procdim.ipx = dim.ipx
                #                    procdim.ipy = dim.ipy

                mxloc = procdim.mx
                myloc = procdim.my
                mzloc = procdim.mz

                # Read the data.
                file_name = os.path.join(datadir, directory, var_file)
                infile = FortranFile(file_name)
                if not run2D:
                    f_loc = dtype(infile.read_record(dtype=read_precision))
                    f_loc = f_loc.reshape((-1, mzloc, myloc, mxloc))
                else:
                    if dim.ny == 1:
                        f_loc = dtype(infile.read_record(dtype=read_precision))
                        f_loc = f_loc.reshape((-1, mzloc, mxloc))
                    else:
                        f_loc = dtype(infile.read_record(dtype=read_precision))
                        f_loc = f_loc.reshape((-1, myloc, mxloc))
                raw_etc = infile.read_record(dtype=read_precision)
                if lpersist:
                    persist(self, infile=infile, precision=read_precision, quiet=quiet)
                infile.close()

                t = raw_etc[0]
                x_loc = raw_etc[1 : mxloc + 1]
                y_loc = raw_etc[mxloc + 1 : mxloc + myloc + 1]
                z_loc = raw_etc[mxloc + myloc + 1 : mxloc + myloc + mzloc + 1]
                if param.lshear:
                    shear_offset = 1
                    deltay = raw_etc[-1]
                else:
                    shear_offset = 0

                dx = raw_etc[-3 - shear_offset]
                dy = raw_etc[-2 - shear_offset]
                dz = raw_etc[-1 - shear_offset]

                if len(proc_dirs) > 1:
                    # Calculate where the local processor will go in
                    # the global array.
                    #
                    # Don't overwrite ghost zones of processor to the
                    # left (and accordingly in y and z direction -- makes
                    # a difference on the diagonals)
                    #
                    # Recall that in NumPy, slicing is NON-INCLUSIVE on
                    # the right end, ie, x[0:4] will slice all of a
                    # 4-digit array, not produce an error like in idl.

                    if procdim.ipx == 0:
                        i0x = 0
                        i1x = i0x + procdim.mx
                        i0xloc = 0
                        i1xloc = procdim.mx
                    else:
                        i0x = procdim.ipx * procdim.nx + procdim.nghostx
                        i1x = i0x + procdim.mx - procdim.nghostx
                        i0xloc = procdim.nghostx
                        i1xloc = procdim.mx

                    if procdim.ipy == 0:
                        i0y = 0
                        i1y = i0y + procdim.my
                        i0yloc = 0
                        i1yloc = procdim.my
                    else:
                        i0y = procdim.ipy * procdim.ny + procdim.nghosty
                        i1y = i0y + procdim.my - procdim.nghosty
                        i0yloc = procdim.nghosty
                        i1yloc = procdim.my

                    if procdim.ipz == 0:
                        i0z = 0
                        i1z = i0z + procdim.mz
                        i0zloc = 0
                        i1zloc = procdim.mz
                    else:
                        i0z = procdim.ipz * procdim.nz + procdim.nghostz
                        i1z = i0z + procdim.mz - procdim.nghostz
                        i0zloc = procdim.nghostz
                        i1zloc = procdim.mz

                    x[i0x:i1x] = x_loc[i0xloc:i1xloc]
                    y[i0y:i1y] = y_loc[i0yloc:i1yloc]
                    z[i0z:i1z] = z_loc[i0zloc:i1zloc]

                    if not run2D:
                        self.f[:, i0z:i1z, i0y:i1y, i0x:i1x] = f_loc[
                            :, i0zloc:i1zloc, i0yloc:i1yloc, i0xloc:i1xloc
                        ]
                    else:
                        if dim.ny == 1:
                            self.f[:, i0z:i1z, i0x:i1x] = f_loc[
                                :, i0zloc:i1zloc, i0xloc:i1xloc
                            ]
                        else:
                            self.f[i0z:i1z, i0y:i1y, i0x:i1x] = f_loc[
                                i0zloc:i1zloc, i0yloc:i1yloc, i0xloc:i1xloc
                            ]
                else:
                    self.f = f_loc
                    x = x_loc
                    y = y_loc
                    z = z_loc
        else:
            raise NotImplementedError(
                "IO strategy {} not supported by the Python module.".format(
                    param.io_strategy
                )
            )

        aatest = []
        uutest = []
        for key in index.__dict__.keys():
            if "aatest" in key:
                aatest.append(key)
            if "uutest" in key:
                uutest.append(key)
        if magic is not None:
            """
            In the functions curl and curl2, the arguments (dx,dy,dz,x,y) are ignored when grid is not None. Nevertheless, we pass them below to take care of the case where the user is trying to read a snapshot without the corresponding grid.dat being present (such as in the test test_read_var).
            """
            if "bb" in magic:
                # Compute the magnetic field before doing trimall.
                aa = self.f[index.ax - 1 : index.az, ...]
                self.bb = dtype(
                    curl(
                        aa,
                        dx=dx,
                        dy=dy,
                        dz=dz,
                        x=x,
                        y=y,
                        run2D=run2D,
                        coordinate_system=param.coord_system,
                        grid=grid,
                    )
                )
                if trimall:
                    self.bb = self.bb[
                        :, dim.n1 : dim.n2 + 1, dim.m1 : dim.m2 + 1, dim.l1 : dim.l2 + 1
                    ]
            if "bbtest" in magic:
                if lh5:
                    # Compute the magnetic field before doing trimall.
                    for j in range(int(len(aatest) / 3)):
                        key = aatest[j*3][:-1]
                        value = index.__dict__[aatest[j*3]]
                        aa = self.f[value - 1 : value + 2, ...]
                        bb = dtype(
                            curl(
                                aa,
                                dx=dx,
                                dy=dy,
                                dz=dz,
                                x=x,
                                y=y,
                                run2D=run2D,
                                coordinate_system=param.coord_system,
                                grid=grid,
                            )
                        )
                        if trimall:
                            setattr(self,"bb"+key[2:],bb[
                                :, dim.n1 : dim.n2 + 1, dim.m1 : dim.m2 + 1, dim.l1 : dim.l2 + 1
                            ])
                        else:
                            setattr(self,"bb"+key[2:],bb)
                else:
                    if hasattr(index, "aatest1"):
                        naatest = int(len(aatest) / 3)
                        for j in range(0, naatest):
                            key = "aatest" + str(np.mod(j + 1, naatest))
                            value = index.__dict__["aatest1"] + 3 * j
                            aa = self.f[value - 1 : value + 2, ...]
                            bb = dtype(
                                curl(
                                    aa,
                                    dx=dx,
                                    dy=dy,
                                    dz=dz,
                                    x=x,
                                    y=y,
                                    run2D=run2D,
                                    coordinate_system=param.coord_system,
                                    grid=grid,
                                )
                            )
                            if trimall:
                                setattr(self,"bb"+key[2:],bb[
                                    :, dim.n1 : dim.n2 + 1, dim.m1 : dim.m2 + 1, dim.l1 : dim.l2 + 1
                                ])
                            else:
                                setattr(self,"bb"+key[2:],bb)
            if "jj" in magic:
                # Compute the electric current field before doing trimall.
                aa = self.f[index.ax - 1 : index.az, ...]
                self.jj = dtype(
                    curl2(
                        aa,
                        dx=dx,
                        dy=dy,
                        dz=dz,
                        x=x,
                        y=y,
                        coordinate_system=param.coord_system,
                        grid=grid,
                    )
                )
                if trimall:
                    self.jj = self.jj[
                        :, dim.n1 : dim.n2 + 1, dim.m1 : dim.m2 + 1, dim.l1 : dim.l2 + 1
                    ]
            if "vort" in magic:
                # Compute the vorticity field before doing trimall.
                uu = self.f[index.ux - 1 : index.uz, ...]
                self.vort = dtype(
                    curl(
                        uu,
                        dx=dx,
                        dy=dy,
                        dz=dz,
                        x=x,
                        y=y,
                        run2D=run2D,
                        coordinate_system=param.coord_system,
                        grid=grid,
                    )
                )
                if trimall:
                    if run2D:
                        if dim.nz == 1:
                            self.vort = self.vort[
                                :, dim.m1 : dim.m2 + 1, dim.l1 : dim.l2 + 1
                            ]
                        else:
                            self.vort = self.vort[
                                :, dim.n1 : dim.n2 + 1, dim.l1 : dim.l2 + 1
                            ]
                    else:
                        self.vort = self.vort[
                            :,
                            dim.n1 : dim.n2 + 1,
                            dim.m1 : dim.m2 + 1,
                            dim.l1 : dim.l2 + 1,
                        ]

        # Trim the ghost zones of the global f-array if asked.
        if trimall:
            self.x = x[dim.l1 : dim.l2 + 1]
            self.y = y[dim.m1 : dim.m2 + 1]
            self.z = z[dim.n1 : dim.n2 + 1]
            if not run2D:
                self.f = self.f[
                    :, dim.n1 : dim.n2 + 1, dim.m1 : dim.m2 + 1, dim.l1 : dim.l2 + 1
                ]
            else:
                if dim.ny == 1:
                    self.f = self.f[:, dim.n1 : dim.n2 + 1, dim.l1 : dim.l2 + 1]
                else:
                    self.f = self.f[:, dim.m1 : dim.m2 + 1, dim.l1 : dim.l2 + 1]
        else:
            self.x = x
            self.y = y
            self.z = z
            self.l1 = dim.l1
            self.l2 = dim.l2 + 1
            self.m1 = dim.m1
            self.m2 = dim.m2 + 1
            self.n1 = dim.n1
            self.n2 = dim.n2 + 1

        # Assign an attribute to self for each variable defined in
        # 'data/index.pro' so that e.g. self.ux is the x-velocity
        for key in index.__dict__.keys():
            if (
                key != "global_gg"
                and key != "keys"
                and "aatest" not in key
                and "uutest" not in key
            ):
                value = index.__dict__[key]
                setattr(self, key, self.f[value - 1, ...])
        # Special treatment for vector quantities.
        if hasattr(index, "ux"):
            setattr(self, "uu", self.f[index.ux - 1 : index.uz, ...])
        if hasattr(index, "ax"):
            setattr(self, "aa", self.f[index.ax - 1 : index.az, ...])
        if hasattr(index, "uu_sph"):
            self.uu_sph = self.f[index.uu_sphx - 1 : index.uu_sphz, ...]
        if hasattr(index, "bb_sph"):
            self.bb_sph = self.f[index.bb_sphx - 1 : index.bb_sphz, ...]
        # Special treatment for test method vector quantities.
        # Note index 1,2,3,...,0 last vector may be the zero field/flow
        if not lh5:
            if hasattr(index, "aatest1"):
                naatest = int(len(aatest) / 3)
                for j in range(0, naatest):
                    key = "aatest" + str(np.mod(j + 1, naatest))
                    value = index.__dict__["aatest1"] + 3 * j
                    setattr(self, key, self.f[value - 1 : value + 2, ...])
            if hasattr(index, "uutest1"):
                nuutest = int(len(uutest) / 3)
                for j in range(0, nuutest):
                    key = "uutest" + str(np.mod(j + 1, nuutest))
                    value = index.__dict__["uutest"] + 3 * j
                    setattr(self, key, self.f[value - 1 : value + 2, ...])
        else:
            #Dummy operation to be corrected
            for j in range(int(len(aatest) / 3)):
                key = aatest[j*3][:-1]
                value = index.__dict__[aatest[j*3]]
                setattr(self, key, self.f[value - 1 : value + 2, ...])
            for j in range(int(len(uutest) / 3)):
                key = uutest[j*3][:-1]
                value = index.__dict__[uutest[j*3]]
                setattr(self, key, self.f[value - 1 : value + 2, ...])


        self.t = t
        self.dx = dx
        self.dy = dy
        self.dz = dz
        if param.lshear:
            self.deltay = deltay

        # Do the rest of magic after the trimall (i.e. no additional curl.)
        self.magic = magic
        if self.magic is not None:
            self.magic_attributes(param, dtype=dtype)

    def __natural_sort(self, procs_list):
        """
        Sort array in a more natural way, e.g. 9VAR < 10VAR
        """

        import re

        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split("([0-9]+)", key)]
        return sorted(procs_list, key=alphanum_key)

    def magic_attributes(self, param, dtype=np.float64):
        """
        Compute some additional 'magic' quantities.
        """

        import sys

        for field in self.magic:
            if field == "rho" and not hasattr(self, "rho"):
                if hasattr(self, "lnrho"):
                    setattr(self, "rho", np.exp(self.lnrho))
                else:
                    raise AttributeError("Problem in magic: lnrho is missing")

            if field == "tt" and not hasattr(self, "tt"):
                if hasattr(self, "lnTT"):
                    tt = np.exp(self.lnTT)
                    setattr(self, "tt", tt)
                else:
                    if hasattr(self, "ss"):
                        if hasattr(self, "lnrho"):
                            lnrho = self.lnrho
                        elif hasattr(self, "rho"):
                            lnrho = np.log(self.rho)
                        else:
                            raise AttributeError(
                                "Problem in magic: missing rho or" + " lnrho variable"
                            )
                        cp = param.cp
                        gamma = param.gamma
                        cs20 = param.cs0 ** 2
                        lnrho0 = np.log(param.rho0)
                        lnTT0 = np.log(cs20 / (cp * (gamma - 1.0)))
                        lnTT = (
                            lnTT0
                            + gamma / cp * self.ss
                            + (gamma - 1.0) * (lnrho - lnrho0)
                        )
                        setattr(self, "tt", dtype(np.exp(lnTT)))
                    else:
                        raise AttributeError("Problem in magic: ss is missing ")

            if field == "ss" and not hasattr(self, "ss"):
                cp = param.cp
                gamma = param.gamma
                cs20 = param.cs0 ** 2
                lnrho0 = np.log(param.rho0)
                lnTT0 = np.log(cs20 / (cp * (gamma - 1.0)))
                if hasattr(self, "lnTT"):
                    setattr(
                        self,
                        "ss",
                        dtype(
                            cp
                            / gamma
                            * (
                                self.lnTT
                                - lnTT0
                                - (gamma - 1.0) * (self.lnrho - lnrho0)
                            )
                        ),
                    )
                elif hasattr(self, "tt"):
                    setattr(
                        self,
                        "ss",
                        dtype(
                            cp
                            / gamma
                            * (
                                np.log(self.tt)
                                - lnTT0
                                - (gamma - 1.0) * (self.lnrho - lnrho0)
                            )
                        ),
                    )
                else:
                    raise AttributeError("Problem in magic: missing lnTT or tt")

            if field == "pp" and not hasattr(self, "pp"):
                cp = param.cp
                gamma = param.gamma
                cv = cp / gamma
                cs20 = param.cs0 ** 2
                lnrho0 = np.log(param.rho0)
                rho0 = param.rho0
                if hasattr(self, "lnrho"):
                    lnrho = self.lnrho
                elif hasattr(self, "rho"):
                    lnrho = np.log(self.rho)
                else:
                    raise AttributeError("Problem in magic: missing rho or lnrho variable")
                if hasattr(self, "ss"):
                    setattr(
                        self,
                        "pp",
                        dtype(
                            (rho0 * cs20 / gamma)
                            * np.exp(gamma * (self.ss + lnrho - lnrho0))
                        ),
                    )
                elif hasattr(self, "lntt"):
                    setattr(self, "pp", dtype((cp - cv) * np.exp(self.lnTT + lnrho)))
                elif hasattr(self, "tt"):
                    setattr(self, "pp", dtype((cp - cv) * self.TT * np.exp(lnrho)))
                else:
                    raise AttributeError("Problem in magic: missing ss or lntt or tt")
