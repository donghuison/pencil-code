!  -*-f90-*-  (for emacs)    vim:set filetype=fortran:  (for vim)

  private

  public :: ilnrho_ss, ilnrho_ee, ilnrho_pp
  public :: ilnrho_lnTT, ilnrho_cs2
  public :: irho_cs2, irho_ss, irho_lnTT, ilnrho_TT
  public :: irho_TT, ipp_ss, ipp_cs2
  public :: irho_eth, ilnrho_eth, irho_ee, irho_pp

  public :: eoscalc,pressure_gradient,temperature_gradient
  public :: temperature_laplacian, get_gamma_etc
  public :: get_soundspeed
  public :: getmu
  public :: getdensity, gettemperature, getpressure
  public :: get_average_pressure

  public :: register_eos
  public :: initialize_eos, units_eos
  public :: rprint_eos, get_slices_eos
  public :: read_eos_init_pars, write_eos_init_pars
  public :: read_eos_run_pars,  write_eos_run_pars
  public :: eos_before_boundary

  public :: select_eos_variable

  public :: pencil_criteria_eos, pencil_interdep_eos
  public :: calc_pencils_eos

  public :: ioncalc, init_eos
  public :: temperature_hessian

! Boundary conditions
  public :: bc_ss_flux,bc_ss_flux_turb,bc_ss_flux_turb_x
  public :: bc_ss_flux_condturb_x, bc_ss_flux_condturb_z
  public :: bc_ss_flux_condturb_mean_x, bc_ism
!
  public :: bc_ss_temp_old,bc_ss_energy
  public :: bc_ss_temp_x, bc_ss_temp_y, bc_ss_temp_z
  public :: bc_ss_temp2_z, bc_ss_temp3_z
  public :: bc_ss_stemp_x,bc_ss_stemp_y,bc_ss_stemp_z
  public :: bc_lnrho_temp_z,bc_lnrho_pressure_z
  public :: bc_stellar_surface
  public :: bc_lnrho_hds_z_iso,bc_lnrho_hdss_z_iso
  public :: bc_lnrho_cfb_r_iso
  public :: bc_ss_a2stemp_x,bc_ss_a2stemp_y,bc_ss_a2stemp_z
! Initial conditions
  public :: isothermal_entropy,isothermal_lnrho_ss
  public :: get_stratz
  public :: pushpars2c

!ajwm SHOULDN'T BE PUBLIC
  public :: cs0,cs20,lnrho0,rho0,lnTT0
!Shouldn't be public, certainly means don't add anymore!!
!,mu,Rgas    BREAKS THE AUTO-TEST

  public :: cs2top,cs2bot

! chemistry
  public :: Pr_number, cp_const, lpres_grad, imass
!  public :: B_n, alpha_n, E_an, low_coeff,high_coeff,troe_coeff,a_k4
!  public :: Mplus_case, tran_data
!
  interface eoscalc              ! Overload subroutine eoscalc
    module procedure eoscalc_farray
    module procedure eoscalc_pencil
    module procedure eoscalc_point
    module procedure eoscalc_point_f
  endinterface
!
  interface pressure_gradient    ! Overload subroutine pressure_gradient
    module procedure pressure_gradient_farray
    module procedure pressure_gradient_point
  endinterface
!
  interface calc_pencils_eos
    module procedure calc_pencils_eos_pencpar
    module procedure calc_pencils_eos_std
  endinterface calc_pencils_eos
