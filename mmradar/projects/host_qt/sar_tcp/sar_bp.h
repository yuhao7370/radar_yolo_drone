#ifndef SAR_BP_H
#define SAR_BP_H

#include <QObject>
#include <iostream>
#include <complex>
#include <QThread>
#include "fftw3.h"



class sar_bp : public QThread
{
    Q_OBJECT
public:
    sar_bp(uint16_t trip_len,uint32_t trip_num,
                  double*pos,uint16_t** trip,
                  double x,double y,double w,double h,
                  uint32_t x_num,uint32_t y_num);
    uint32_t get_trip_num(void);
    uint32_t get_process(void);
    void get_process_img(void);
    uint16_t m_trip_len;
    uint32_t m_trip_num;
    double* m_pos;
    uint16_t** m_trip;
    double m_x;
    double m_y;
    double m_w;
    double m_h;
    uint32_t m_x_num;
    uint32_t m_y_num;
    uint32_t m_now_trip;//当前正在处理的trip索引


    void run(void) override;

    ~sar_bp();


signals:
    void get_img(std::complex<double>*img,uint32_t x_num,uint32_t y_num);
    void finish_img(std::complex<double>*img,uint32_t x_num,uint32_t y_num);

};

#endif // SAR_BP_H
