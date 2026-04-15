#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include<QTcpServer>//监听套接字
#include<QTcpSocket>//通信套接字
#include<QDebug>
#include <QTimer>
#include<QByteArray>
#include <QFile>
#include <QTimer>
#include <QPainter>
#include <QMouseEvent>
#include <QInputDialog>

#include "sar_bp.h"
#include "sar_bp_1d.h"
#include "sar_data_cleaner.h"
#include "fftw3.h"
#include "anim_dsg.h"

#define file_path "E:/mmradar/data/"
#define bp_test_file "E:/mmradar/data/"
#define sar_noise_clean_file "E:/mmradar/sar_noise_500M.bin"
//#define sar_noise_clean_file "D:/Desktop/毕设/数据/sar_noise_250M.bin"
#define FFT_REAL



QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();
    QTcpServer *tcpserver;
    QTcpSocket *tcpsocket;
    long speed_cnt;

    uint16_t* sar_data[4];
    uint8_t* sar_mux;
    uint32_t sar_look_num;

    sar_bp* sar_bp1;
    sar_data_cleaner* sar_data_cleaner1;
    sar_bp_1d *sar_bp_1d_1;
    int mean;
    uint16_t *sar_noise;
    int sar_noise_len;


#ifdef FFT_REAL
    double *fft_in[4];
    double *now_trip[4];

#else
    fftw_complex *fft_in[4];

#endif
    fftw_complex *fft_out[4];
    bool now_buf;
    QByteArray look_buf;
    int zero_time;//FFT补零倍数


public slots:
    void timeout(void);
    void getData(QByteArray res);
    void clean_finish(QString file_name);

signals:
    void get_data(QByteArray res);

private slots:
    void on_btn_start_clicked();

    void on_pushButton_clicked();

    void on_bp_start_clicked();

    void on_img_start_clicked();

    void get_img(QImage res,QImage dist_img);

    void on_horizontalSlider_sliderReleased();

    void on_file_idx_clicked();

    void on_set_file_idx_clicked();

private:
    Ui::MainWindow *ui;
    int rec_sta;
    int look_sta;
    uint32_t rec_cnt;
    uint32_t err_time_cnt;
    uint32_t fps;
    QFile* sar_file;
    void file_open(void);
    void file_write(QByteArray dat);
    void file_close(void);
    void set_noise_clean_file(QString file);
    QString now_file;
    int file_idx;

protected:
    void paintEvent(QPaintEvent *event);
    void mousePressEvent(QMouseEvent *event);
    anim_dsg* anim_ds1;



};
#endif // MAINWINDOW_H
