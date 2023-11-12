! $Id$
!
! MODULE_DOC: This module contains GPU related types and functions to be used with the ASTAROTH nucleus.
!
! CPARAM logical, parameter :: lgpu = .true.
!
!**************************************************************************
!
module GPU
!
  use Cdata
  use General, only: keep_compiler_quiet
  use Mpicomm, only: stop_it

  implicit none

  external initialize_gpu_c
  external finalize_gpu_c
  external rhs_gpu_c
  external copy_farray_c

  include 'gpu.h'

  integer(KIND=ikind8) :: pFarr_GPU_in, pFarr_GPU_out
  
contains

!***********************************************************************
    subroutine initialize_GPU
!
      character(LEN=512) :: str
!
      str=''
      if (lanelastic) str=trim(str)//', '//'anelastic'
      if (lboussinesq) str=trim(str)//', '//'boussinesq'
      !if (lenergy) str=trim(str)//', '//'energy'
      if (ltemperature) str=trim(str)//', '//'temperature'
      if (lshock) str=trim(str)//', '//'shock'
      if (lgrav) str=trim(str)//', '//'gravity'
      if (lheatflux) str=trim(str)//', '//'heatflux'
      if (lhyperresistivity_strict) str=trim(str)//', '//'hyperresi_strict'
      if (lhyperviscosity_strict) str=trim(str)//', '//'hypervisc_strict'
      if (lADI) str=trim(str)//', '//'implicit_physics'
      if (llorenz_gauge) str=trim(str)//', '//'lorenz_gauge'
      if (ldustvelocity) str=trim(str)//', '//'dustvelocity'
      if (ldustdensity) str=trim(str)//', '//'dustdensity'
      if (ltestscalar) str=trim(str)//', '//'testscalar'
      if (ltestfield) str=trim(str)//', '//'testfield'
      if (ltestflow) str=trim(str)//', '//'testflow'
      if (linterstellar) str=trim(str)//', '//'interstellar'
      if (lcosmicray) str=trim(str)//', '//'cosmicray'
      if (lcosmicrayflux) str=trim(str)//', '//'cosmicrayflux'
      if (lshear) str=trim(str)//', '//'shear'
      if (lpscalar) str=trim(str)//', '//'pscalar'
      if (lascalar) str=trim(str)//', '//'ascalar'
      if (lradiation) str=trim(str)//', '//'radiation'
      if (lchemistry) str=trim(str)//', '//'chemistry'
      if (lchiral) str=trim(str)//', '//'chiral'
      if (ldetonate) str=trim(str)//', '//'detonate'
      if (lneutralvelocity) str=trim(str)//', '//'neutralvelocity'
      if (lneutraldensity) str=trim(str)//', '//'neutraldensity'
      if (lopacity) str=trim(str)//', '//'opacity'
      if (lpolymer) str=trim(str)//', '//'polymer'
      if (lpointmasses) str=trim(str)//', '//'pointmasses'
      if (lpoisson) str=trim(str)//', '//'poisson'
      if (lselfgravity) str=trim(str)//', '//'selfgravity'
      if (lsolid_cells) str=trim(str)//', '//'solid_cells'
      if (lspecial) str=trim(str)//', '//'special'
      if (lpower_spectrum) str=trim(str)//', '//'power_spectrum'
      if (lparticles) str=trim(str)//', '//'particles'

      if (str/='') call stop_it('No GPU implementation for module(s) "'//trim(str(3:))//'"')
!
      call initialize_gpu_c(pFarr_GPU_in,pFarr_GPU_out)
!print'(a,1x,Z0,1x,Z0)', 'pFarr_GPU_in,pFarr_GPU_out=', pFarr_GPU_in,pFarr_GPU_out
    endsubroutine initialize_GPU
!**************************************************************************
    subroutine gpu_init
!
      call init_gpu_c
!
    endsubroutine gpu_init
!**************************************************************************
    subroutine register_GPU(f)
!
      real, dimension(:,:,:,:), intent(IN) :: f

      call register_gpu_c(f)
!
    endsubroutine register_GPU
!**************************************************************************
    subroutine finalize_GPU
!
      call finalize_gpu_c
!
    endsubroutine finalize_GPU
!**************************************************************************
    subroutine rhs_GPU(f,isubstep,early_finalize)
!
      use General, only: notanumber

      real, dimension (mx,my,mz,mfarray), intent(INOUT) :: f
      integer,                            intent(IN)    :: isubstep
      logical,                            intent(IN)    :: early_finalize
!
      integer :: ll, mm, nn
      real :: val
      logical, save :: lvery_first=.true.

      goto 1
      val=1.
      do nn=1,mz
        do mm=1,my
          do ll=1,mx
            f(ll,mm,nn,iux)=val; val=val+1.
      enddo; enddo; enddo

      print*, 'vor integrate'
      do nn=1,3
        if (notanumber(f(:,:,nn,iux))) print*,'NaN in ux, lower z', nn
      enddo
      print*, '---------------'

1     continue
      call rhs_gpu_c(isubstep,lvery_first,early_finalize)
!
      lvery_first=.false.

      return
!
      if (.not.lroot) return
      do nn=1,mz   !  nghost+1,mz-nghost
        print*, 'nn=', nn
        do mm=1,my
          print'(22(1x,f7.0))',f(:,mm,nn,iux)
      enddo; enddo

      do nn=1,3
        if (notanumber(f(:,:,nn,iux))) print*,'NaN in ux, lower z', nn                
      enddo

    endsubroutine rhs_GPU
!**************************************************************************
    subroutine copy_farray_from_GPU(f)

      real, dimension (mx,my,mz,mfarray), intent(OUT) :: f

      call copy_farray_c(f(1,1,1,iux),f(1,1,1,iuy),f(1,1,1,iuz),f(1,1,1,ilnrho))

    endsubroutine copy_farray_from_GPU
!**************************************************************************

    ! subroutine test_rhs(f,df,p,rhs_1,rhs_2)
    !   real, dimension (mx,my,mz,mfarray) :: f
    !   real, dimension (mx,my,mz,mfarray) :: df,df_copy
    !   integer :: i,j,k,n
    !   type (pencil_case) :: p

    !   intent(in) :: f,p
    !   intent(inout) :: df
    !   logical :: passed
    !   interface
    !       subroutine rhs_1(f,df,p)
    !           real, dimension (mx,my,mz,mfarray) :: f
    !           real, dimension (mx,my,mz,mfarray) :: df
    !           type (pencil_case) :: p

    !           intent(in) :: f,p
    !           intent(inout) :: df
    !       endsubroutine rhs_1 
    !       subroutine rhs_2(f,df,p)
    !           real, dimension (mx,my,mz,mfarray) :: f
    !           real, dimension (mx,my,mz,mfarray) :: df
    !           type (pencil_case) :: p

    !           intent(in) :: f,p
    !           intent(inout) :: df
    !       endsubroutine rhs_2 
    !   endinterface
    !   df_copy = df
    !   call rhs_1(df)
    !   call rhs_2(df_copy)
    !   passed = .true.
    !   do i=1,mx
    !     do j=1,my
    !       do k=1,mz
    !         do n=1,mfarray
    !           if df_copy(i,j,k,n) /= df(i,j,k,n) then
    !             print*,"Wrong at: ",i,j,k,n
    !             passed = .false.
    !           endif
    !         enddo
    !       enddo
    !     enddo
    !   enddo
    !   if(passed) then
    !     print*,"passed test :)"
    !   else
    !     print*,"did not pass test :/"
    !   endif
    ! endsubroutine test_rhs
!**************************************************************************
endmodule GPU
