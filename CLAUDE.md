# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Pencil Code is a high-order finite-difference code for compressible hydrodynamic flows with magnetic fields and particles. It is a modular scientific computing framework written primarily in Fortran 90 for computational fluid dynamics and magnetohydrodynamics simulations.

## Essential Commands

### Initial Setup
```bash
# Source the environment (required once per shell session)
source sourceme.sh  # or sourceme.csh for C-shell

# Navigate to a sample simulation
cd samples/conv-slab  # or any other sample

# Create data directory for output
mkdir data
```

### Building and Running Simulations
```bash
# Set up symbolic links to source code
pc_setupsrc

# Build the code (use configuration files from config/hosts/ or config/compilers/)
pc_build              # uses default configuration
pc_build -f os/GNU_Linux  # for Linux with GCC
pc_build -f os/GNU_Linux,mpi/default  # with MPI support

# Create initial conditions
pc_start

# Run the simulation  
pc_run

# For MPI runs
pc_run -np 4  # run with 4 processors
```

### Testing
```bash
# Run auto-tests (different levels of testing)
pc_auto-test         # default level 2
pc_auto-test -l 0    # minimal tests
pc_auto-test -l 1    # important tests
pc_auto-test -l 3    # all tests

# Run Python tests (requires pytest)
python/tests/test-python-modules.py

# Test a specific sample
cd samples/helical-MHDturb
pc_auto-test --pencil-check
```

### Other Important Commands
```bash
# Clean source directory
pc_cleansrc

# Debug run issues
pc_debug

# Check code style
pc_codingstyle

# Create new run directory
pc_newrun <new_directory>

# Compare two runs
pc_diffruns <run1> <run2>
```

## Architecture and Code Organization

### Modular Physics System

The code uses a compile-time modular system where physics modules are selected in `src/Makefile.local`:

- **Core modules**: `grid`, `cdata`, `cparam`, `mpicomm`, `io`, `timestep`
- **Physics modules** (prefix 'no' to disable):
  - `hydro` - Hydrodynamics 
  - `magnetic` - Magnetohydrodynamics
  - `entropy` - Entropy equation
  - `density` - Continuity equation
  - `energy` - Energy equation
  - `viscosity` - Viscous terms
  - `radiation` - Radiative transfer
  - `particles` - Lagrangian particles
  - `chemistry` - Chemical reactions
  - `cosmicray` - Cosmic ray physics
  - `selfgravity` - Self-gravity
  - `shear` - Shearing box

### Pencil Decomposition

The code uses "pencil decomposition" for parallel processing:
- Domain is decomposed in y and z directions across MPI processes
- Each process handles a "pencil" of data in the x-direction
- Ghost zones handle boundary communication between processes
- Key arrays: `f(mx,my,mz,mfarray)` where `mx=nx+2*nghost`, etc.

### Directory Structure

```
pencil-code/
├── src/           # Main source code (Fortran 90 modules)
├── samples/       # Example simulations with reference outputs
├── bin/           # Utility scripts (pc_* commands)
├── config/        # Build configuration files
├── idl/           # IDL analysis routines
├── python/        # Python analysis package (pencil module)
├── doc/           # Documentation and manual
└── tests/         # Test infrastructure
```

### Key Source Files

- `src/run.f90` - Main simulation loop
- `src/start.f90` - Initial condition setup
- `src/cdata.f90` - Global data structures
- `src/cparam.f90` - Compile-time parameters
- `src/equ.f90` - Equation solving routines
- `src/Makefile.local` - Module selection (created per simulation)
- `src/cparam.local` - Dimension parameters (created per simulation)

### Input/Output Files

Each simulation directory contains:
- `start.in` - Initial condition parameters
- `run.in` - Runtime parameters  
- `print.in` - Diagnostic output selection
- `video.in` - Slice output configuration
- `data/` - Output directory containing:
  - `var.dat`, `VAR*` - Snapshot files
  - `time_series.dat` - Time series diagnostics
  - `slices/` - 2D slice data

## Development Patterns

### Adding New Physics

1. Create module files: `mymodule.f90`, `mymodule.h`, `nomymodule.f90`
2. Add module to `src/Makefile` selection system
3. Follow existing module patterns for initialization, evolution, and diagnostics
4. Use pencil_case type for derived quantities

### Fortran Conventions

- Use `real(KIND=rkind8)` for time and units
- Default real precision set by compile flags
- Module variables should be private with public access routines
- Follow existing indentation and naming conventions
- Use `intent(in)`, `intent(out)`, `intent(inout)` for subroutine arguments

### Analysis Workflows

**IDL Analysis**:
```idl
; Start IDL in simulation directory
.r start         ; Initialize grid and parameters
.r r             ; Read var.dat file
.r ts            ; Read time series
```

**Python Analysis**:
```python
import pencil as pc
# Read simulation data
var = pc.read.var()        # Latest snapshot
ts = pc.read.ts()          # Time series
param = pc.read.param()    # Parameters
grid = pc.read.grid()      # Grid information
```

### Performance Considerations

- Use MPI for parallel runs on clusters
- Typical domain decomposition: split in y and z, keep x contiguous
- Ghost zone width affects derivative accuracy (default nghost=3 for 6th order)
- I/O can be expensive - use `io_dist` for distributed I/O
- HDF5 output available with appropriate compilation flags

## Common Issues and Solutions

1. **Module conflicts**: Check `src/Makefile.local` for incompatible module combinations
2. **Ghost zone errors**: Verify boundary conditions in `run.in`
3. **Timestep crashes**: Reduce Courant number or check for numerical instabilities
4. **MPI issues**: Ensure proper MPI configuration in build command
5. **Memory issues**: Adjust grid resolution or use more MPI processes

## Scientific Context

This code is used for astrophysical fluid dynamics simulations including:
- Solar and stellar convection
- Accretion disk dynamics  
- Magnetohydrodynamic turbulence
- Planet formation
- Interstellar medium dynamics
- Dynamo processes

The "pencil" name refers to the domain decomposition strategy, not drawing implements.