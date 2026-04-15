#include "sar_bp.h"

sar_bp::sar_bp(uint16_t trip_len,uint32_t trip_num,
               double*pos,uint16_t** trip,
               double x,double y,double w,double h,
               uint32_t x_num,uint32_t y_num)
{
    m_trip_len=trip_len;
    m_trip_num=trip_num;
    m_pos=pos;
    m_trip=trip;
    m_x=x;
    m_y=y;
    m_w=w;
    m_h=h;
    m_x_num=x_num;
    m_y_num=y_num;
    m_now_trip=0;
}

uint32_t sar_bp::get_trip_num(void)
{
    return m_trip_num;
}
uint32_t sar_bp::get_process(void)
{
    return m_now_trip;
}
void sar_bp::get_process_img(void)
{

}
void sar_bp::run(void)
{

}
sar_bp::~sar_bp()
{

}
