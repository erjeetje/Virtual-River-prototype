# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 11:13:15 2019

@author: HaanRJ
"""

def set_crest_height(model, structure, height, weir_type="groyne"):
    #model.set_compound_field
    """
    subroutine get_compound_field


!> Sets the value for a specific field for a specific item in a set-variable of compound values.
!!
!! For example, all pumping stations in a model may be collected in a single compound variable set, named 'pumps',
!! a single pump selected by its name, and the actual data by its field name.
!!
!! The input value enters as a generic pointer, and will be converted to the required data type, e.g., double.
!! If necessary, use get_compound_field_type and get_compound_field_shape to determine which input is expected.
subroutine set_compound_field(c_var_name, c_item_name, c_field_name, xptr) bind(C, name="set_compound_field")
  !DEC$ ATTRIBUTES DLLEXPORT :: set_compound_field
  use iso_c_binding, only: c_double, c_char, c_loc, c_f_pointer
  use iso_c_utils
  use unstruc_messages
  use m_strucs
  use m_wind

  character(kind=c_char), intent(in) :: c_var_name(*)   !< Name of the set variable, e.g., 'pumps'
  character(kind=c_char), intent(in) :: c_item_name(*)  !< Name of a single item's index/location, e.g., 'Pump01'
  character(kind=c_char), intent(in) :: c_field_name(*) !< Name of the field to get, e.g., 'capacity'
  type(c_ptr), value,     intent(in) :: xptr            !< Pointer (by value) to the C-compatible value data to be set.

  real(c_double), pointer :: x_0d_double_ptr

  integer :: item_index
  integer :: iostat

  ! The fortran name of the attribute name
  character(len=MAXSTRLEN) :: var_name
  character(len=MAXSTRLEN) :: item_name
  character(len=MAXSTRLEN) :: field_name
  ! Store the name
  var_name   = char_array_to_string(c_var_name)
  item_name  = char_array_to_string(c_item_name)
  field_name = char_array_to_string(c_field_name)
   ! Debugging printing only: guess that it's a scalar double value, for now.
   call c_f_pointer(xptr, x_0d_double_ptr)
   write(msgbuf, '(6a,f20.6,a)', iostat=iostat) 'set_compound_field for ', trim(var_name), '(', trim(item_name), ')::', trim(field_name), ', will be set to value = ', x_0d_double_ptr, '.'
   call dbg_flush()
  ! TODO: AvD: include "bmi_set_compound_field.inc"
  select case(var_name)
  ! PUMPS
  case("pumps")
     call getStructureIndex('pumps', item_name, item_index)
     if (item_index == 0) then
         return
     endif
     select case(field_name)
     case("capacity")
         call c_f_pointer(xptr, x_0d_double_ptr)
         qpump(item_index) = x_0d_double_ptr
        return
     end select

  ! WEIRS
  case("weirs")
     call getStructureIndex('weirs', item_name, item_index)
     if (item_index == 0) then
         return
     endif
     select case(field_name)
     case("crest_level", "CrestLevel")
         call c_f_pointer(xptr, x_0d_double_ptr)
         zcgen((item_index-1)*3+1) = x_0d_double_ptr
         return
     case("lat_contr_coeff")
         ! TODO: RTC: AvD: set this in weir params
         return
     end select
     call update_zcgen_widths_and_heights()
    """
    """
    use get_compound_field_type to determine the correct data type.
    subroutine get_compound_field(c_var_name, c_item_name, c_field_name, x) bind(C, name="get_compound_field")
    
    character(kind=c_char), intent(in) :: c_var_name(*)   !< Name of the set variable, e.g., 'pumps'
    character(kind=c_char), intent(in) :: c_item_name(*)  !< Name of a single item's index/location, e.g., 'Pump01'
    character(kind=c_char), intent(in) :: c_field_name(*) !< Name of the field to get, e.g., 'capacity'
    type(c_ptr),            intent(inout) :: x            !< Pointer (by reference) to requested value data, NULL if not available.
    
    integer :: item_index
    
    case("weirs")
    call getStructureIndex('weirs', item_name, item_index)
    if (item_index == 0) then
        return
    endif
    if (item_index <= ncgensg) then 
        ! DFlowFM type structures
        select case(field_name)
        case("crest_level", "CrestLevel")
            x = c_loc(zcgen((item_index-1)*3+1))
            return
        case("lat_contr_coeff")
            ! TODO: RTC: AvD: get this from weir params
            return
        end select
    else
        ! DFlowFM1D type structures
        item_index = item_index - ncgensg
        select case(field_name)
        case("crest_level", "CrestLevel")
            x = get_crest_level_c_loc(network%sts%struct(item_index))  
            return
        case("lat_contr_coeff")
            ! TODO: RTC: AvD: get this from weir params (also for 1d?) 
            return
        end select
    endif
    """
    return