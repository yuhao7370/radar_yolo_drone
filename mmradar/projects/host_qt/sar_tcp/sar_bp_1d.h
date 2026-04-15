#ifndef SAR_BP_1D_H
#define SAR_BP_1D_H

#include <QObject>
#include<QDebug>
#include<QString>
#include <QThread>
#include <QFile>
#include <complex>
#include <QImage>

#include "fftw3.h"

class sar_bp_1d:public QThread
{
    Q_OBJECT
public:
    double m_x,m_y,m_w,m_h;
    int m_x_num,m_y_num;
    bool m_dir;
    QString m_name;
    double m_speed;
    quint64 trip_num;
    int trip_len;
    int zero_times;

    uint16_t *sar_noise;
    int sar_noise_len;
    std::complex<double> **img;

    QString m_res_name;
    bool busy;


    sar_bp_1d();
    void set_geo(double x,double y,double w,double h);//单位：米
    void set_grid(int x_num,int y_num);
    void set_dir(bool dir);//0:right,1:left
    void set_file(QString name);
    void set_speed(double speed);//单位：m/s
    void set_noise_clean_file(QString file);
    QImage get_res_at_level(double level);
    void set_sar_high(double h);
    void run(void) override;

    double sar_high;//雷达高度，设置后成像结果将采用地面坐标系，如果为负数则结果为距离-方位坐标系
    double window(int type, int n, int i);
    void set_res_name(QString res_name);//设置成像结果存储路径+文件名

signals:
    void get_img(QImage res,QImage dist_img);





};

#endif // SAR_BP_1D_H
