#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QDir>
#include <QtGlobal>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    runtime_config = RuntimeConfig::load();
    QDir().mkpath(runtime_config.data_dir);
    clean_file_path = runtime_config.data_file("clean.bin");

    tcpserver=new QTcpServer(this);
    tcpsocket=NULL;
    if (!tcpserver->listen(QHostAddress::Any, runtime_config.listen_port)) {
        qWarning() << "监听端口失败:" << runtime_config.listen_port << tcpserver->errorString();
    }
    speed_cnt=0;
    connect(this,SIGNAL(get_data(QByteArray)),this,SLOT(getData(QByteArray)));

    //服务器建立连接
        connect(tcpserver,&QTcpServer::newConnection,[=](){
            //取出连接好的套接字
            tcpsocket=tcpserver->nextPendingConnection();

            //获得通信套接字的控制信息
            QString ip=tcpsocket->peerAddress().toString();//获取连接的 ip地址
            quint16 port=tcpsocket->peerPort();//获取连接的 端口号
            qDebug()<<QString("[%1:%2] 客服端连接成功").arg(ip).arg(port);
            //接收信息  必须放到连接中的槽函数 不然tcpsocket就是一个野指针
            connect(tcpsocket,&QTcpSocket::readyRead,[=](){
                //从通信套接字中取出内容
                QByteArray res=tcpsocket->readAll();
                if(res.size()==0)
                {
                    tcpsocket=NULL;
                    qDebug()<<"连接断开";
                }
                else
                {
                    speed_cnt+=res.size();
                    emit get_data(res);
                }



            });
        });

        QTimer *timer = new QTimer(this);
        connect(timer, SIGNAL(timeout()), this, SLOT(timeout()));
        timer->start(1000);

        rec_sta=0;
        rec_cnt=0;
        err_time_cnt=0;
        sar_file=NULL;

        look_sta=0;

        sar_look_num=1490*2;
        zero_time=1;

        sar_data[0]=new uint16_t[sar_look_num];
        sar_data[1]=new uint16_t[sar_look_num];
        sar_data[2]=new uint16_t[sar_look_num];
        sar_data[3]=new uint16_t[sar_look_num];
        sar_mux=new uint8_t[sar_look_num];
        look_buf.clear();

#ifdef FFT_REAL
//        fft_in[0]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
//        fft_in[1]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
//        fft_in[2]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
//        fft_in[3]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
        fft_in[0]=(double*)fftw_malloc(sizeof(double) * sar_look_num*zero_time);
        fft_in[1]=(double*)fftw_malloc(sizeof(double) * sar_look_num*zero_time);
        fft_in[2]=(double*)fftw_malloc(sizeof(double) * sar_look_num*zero_time);
        fft_in[3]=(double*)fftw_malloc(sizeof(double) * sar_look_num*zero_time);
        for(int i=0;i<sar_look_num*zero_time;i++)
        {
            for(int j=0;j<4;j++)
            {
                fft_in[j][i]=0;
            }
        }
#else
        fft_in[0]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);
        fft_in[1]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);
        fft_in[2]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);
        fft_in[3]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);
#endif




//        fft_out[0]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);
//        fft_out[1]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);
//        fft_out[2]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);
//        fft_out[3]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num);

        fft_out[0]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num*zero_time);
        fft_out[1]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num*zero_time);
        fft_out[2]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num*zero_time);
        fft_out[3]=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * sar_look_num*zero_time);
        fps=0;


        sar_bp1=new sar_bp(0,0,0,0,0,0,0,0,0,0);
        sar_bp1->start();

        sar_data_cleaner1=new sar_data_cleaner;
        connect(sar_data_cleaner1,SIGNAL(clean_finish(QString)),this,SLOT(clean_finish(QString)));
        sar_bp_1d_1=new sar_bp_1d();
        sar_bp_1d_1->set_file(clean_file_path);
        sar_bp_1d_1->set_res_name(data_file("res.jpg"));

        connect(sar_bp_1d_1,SIGNAL(get_img(QImage,QImage)),this,SLOT(get_img(QImage,QImage)));
        mean=0;

        sar_noise=NULL;
        sar_noise_len=0;

        set_noise_clean_file(runtime_config.noise_file);

        ui->lineEdit->setText(QString::number(runtime_config.target_size_kb));
        ui->horizontalSlider->setValue(
            qBound(
                ui->horizontalSlider->minimum(),
                qRound(runtime_config.contrast_level),
                ui->horizontalSlider->maximum()
            )
        );

        now_trip[0]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
        now_trip[1]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
        now_trip[2]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
        now_trip[3]=(double*)fftw_malloc(sizeof(double) * sar_look_num);
        for(int i=0;i<sar_look_num;i++)
        {
            for(int j=0;j<4;j++)
            {
                now_trip[j][i]=0;
            }
        }

        anim_ds1=new anim_dsg();


        file_idx=0;
        now_file=data_file("sar_1.bin");


//        for(int i=1;i<=31;i++)
//        {
//            qDebug()<<"正在处理文件"<<QString("sar_%1.bin").arg(i);
//            QString tmp_file=data_file(QString("sar_%1.bin").arg(i));
//            sar_data_cleaner1->set_input_file(tmp_file);
//            sar_data_cleaner1->set_output_file(clean_file_path);
//            sar_data_cleaner1->start();
//            sar_data_cleaner1->busy=1;
//            while(sar_data_cleaner1->busy)
//            {
//                this->update();
//            }




//            qDebug()<<QString("sar_%1.bin").arg(i)<<"清洗完成，正在成像";
//            sar_bp_1d_1->set_res_name(data_file(QString("res_%1.jpg").arg(i)));
//            sar_bp_1d_1->set_noise_clean_file(runtime_config.noise_file);
//            sar_bp_1d_1->set_dir(0);
//            sar_bp_1d_1->set_geo(runtime_config.img_x, runtime_config.img_y, runtime_config.img_w, runtime_config.img_h);
//            sar_bp_1d_1->set_grid(runtime_config.grid_x, runtime_config.grid_y);
//            sar_bp_1d_1->set_sar_high(runtime_config.sar_height);
//            sar_bp_1d_1->set_file(clean_file_path);
//            sar_bp_1d_1->set_speed(runtime_config.speed);
//            sar_bp_1d_1->busy=1;
//            sar_bp_1d_1->start();
//            while(sar_bp_1d_1->busy)
//            {
//                this->update();
//            }
//            sar_bp_1d_1->busy=1;
//            sar_bp_1d_1->get_res_at_level(6764);
//            while(sar_bp_1d_1->busy)
//            {
//                this->update();
//            }


//        }




}
void MainWindow::paintEvent(QPaintEvent *event)
{


    QPainter painter(this);
    painter.setPen(QPen(Qt::red, 10));
    for(int i=0;i<sar_look_num/2-1;i++)
    {
        painter.drawLine(i+200,now_trip[0][(int)(2*i)]/15+400,i+1+200,now_trip[0][(int)(2*(i+1))]/15+400);
    }



    double now_dot=0;
    double max_dot=0;
    int max_idx=0;

    painter.setPen(QPen(Qt::blue, 10));
    for(int i=0;i<(sar_look_num-1);i++)
    {
        now_dot=sqrt(fft_out[0][i][0]*fft_out[0][i][0]+fft_out[0][i][1]*fft_out[0][i][1]);
        painter.drawLine(200+50*i/zero_time,700+now_dot/20000,200+50*(i+1)/zero_time,700+sqrt(fft_out[0][i+1][0]*fft_out[0][i+1][0]+fft_out[0][i+1][1]*fft_out[0][i+1][1])/20000);
//        if(i>20*zero_time/10)
//        {
//            if(now_dot>max_dot)
//            {
//                max_dot=now_dot;
//                max_idx=i;
//            }
//        }
        if(i<30*zero_time)
        {
            if(now_dot*(i)>max_dot*(max_idx))
            {
                max_dot=now_dot;
                max_idx=i;
            }
        }



    }

    painter.setPen(QPen(Qt::red, 5));
    painter.setFont(QFont("Arial", 40));
    painter.drawText(50*max_idx/zero_time-5,750+max_dot/20000-5,QString("距离:%1m").arg(max_idx*0.30208717/zero_time));
    painter.drawEllipse(200+50*max_idx/zero_time-5,700+max_dot/20000-5,10,10);

    painter.setPen(QPen(Qt::red, 5));
    painter.setFont(QFont("Arial", 30));
    painter.drawText(10,300,"时域波形");

    painter.setPen(QPen(Qt::blue, 5));
    painter.setFont(QFont("Arial", 30));
    painter.drawText(10,750,"距离像");




//    painter.setPen(QPen(Qt::blue, 2));
//    for(int i=0;i<(sar_look_num-1);i++)
//    {
//        painter.drawLine(50*i/zero_time,150+100*atan(fft_out[0][i][1]/fft_out[0][i][0]),50*(i+1)/zero_time,150+100*atan(fft_out[0][i+1][1]/fft_out[0][i+1][0]));
//    }

//    painter.setPen(QPen(Qt::green, 2));
//    for(int i=0;i<(sar_look_num-1);i++)
//    {
//        painter.drawLine(50*i,500+100*atan(fft_out[0][i][1]/fft_out[0][i][0]),50*(i+1),500+100*atan(fft_out[0][i+1][1]/fft_out[0][i+1][0]));
//    }


}
void MainWindow::mousePressEvent(QMouseEvent *event)

{

    QPoint pos = event->pos();

    qDebug() << "X=" << pos.x();

}


MainWindow::~MainWindow()
{
    delete ui;
}
void MainWindow::timeout(void)
{
    if(speed_cnt!=0)
    {
        qDebug()<<QString("speed=[%1]MB/s,err=[%2]time,fps=[%3] hz/s").arg((float)speed_cnt/1024/1024).arg(err_time_cnt).arg(fps);
    }

    speed_cnt=0;
    err_time_cnt=0;
    fps=0;
}
void MainWindow::getData(QByteArray res)
{
    if(rec_sta==1)
    {
        rec_cnt+=res.size();
        file_write(res);
        if( (rec_cnt/1024) > (ui->lineEdit->text().toULongLong()))
        {
            rec_sta=0;
            ui->btn_start->setText("开始");
            file_close();
            if(look_sta==0)
            {
                tcpsocket->write(QString("stop").toLocal8Bit());
            }

            rec_cnt=0;
        }
    }

    if(look_sta==1)
    {
        look_buf.append(res);
        if((uint32_t)(look_buf.size())>=((sar_look_num*3)*8))//8是8字节，3是3倍长度
        {
            //tcpsocket->write(QString("stop").toLocal8Bit());
            //tcpsocket->flush();

            uint16_t* tmp_dat=(uint16_t*)look_buf.data();
            int tmp_len=look_buf.size()/2;
            int before_i=0;
            int err_time=-1;
            int now_ch=-1;
            int now_cnt=0;
            int start_down_cnt=-1;
            bool pre_mux=tmp_dat[0]&0x0002;
            for(int i=0;i<tmp_len;i++)
            {
                if(tmp_dat[i]&0x0001) //判断
                {
                    if((i-before_i)!=4)
                    {
                        err_time++;
                    }
                    before_i=i;
                }

                if(now_ch==-1)
                {

                    if( pre_mux!=((tmp_dat[i]&0x0002)>>1) )
                    {
                        //now_ch=1;
                        start_down_cnt=36;
                    }
                    pre_mux=((tmp_dat[i]&0x0002)>>1);
                    if(start_down_cnt!=-1)
                    {
                        start_down_cnt--;
                        if(start_down_cnt==0)
                        {
                            now_ch=3;
                        }
                    }
                }
                else
                {
                    if(now_ch<=4)
                    {
                        sar_data[now_ch-1][now_cnt]=(tmp_dat[i]&0xFFFC)/4;//右移两位
                        now_ch++;
                    }


                    if(tmp_dat[i]&0x0001)
                    {
                        sar_mux[now_cnt]=tmp_dat[i]&0x0002;
                        now_ch=1;
                        now_cnt++;
                        if(now_cnt>=sar_look_num)
                        {
                            break;
                        }

                    }
                }
            }
            if(err_time!=0)
            {
                err_time_cnt++;
            }

            look_buf.clear();







            if(err_time<10)
            {
                uint64_t sum=0;

#ifdef FFT_REAL
            for(int i=0;i<sar_look_num;i++)
            {
                fft_in[0][i]=sar_data[0][i];//
                int a = sizeof(fft_in[0][i]);
                int b = sizeof(sar_data[0][i]);
                sum+=fft_in[0][i];
            }
            mean=sum/sar_look_num;
            if(1)
            {
                if(sar_noise==NULL)
                {
                    for(int i=0;i<sar_look_num;i++)
                    {
                        fft_in[0][i]-=mean;
                        now_trip[0][i]=fft_in[0][i];
                    }

                }
                else
                {
                    for(int i=0;i<sar_look_num;i++)
                    {
                        if(i+9<sar_noise_len)
                        {
                           fft_in[0][i]-=sar_noise[i+9];
                        }
                        else
                        {
                            fft_in[0][i]-=mean;
                        }
                        now_trip[0][i]=fft_in[0][i];
                    }
                }
            }
            else
            {
                for(int i=0;i<sar_look_num;i++)
                {
                     now_trip[0][i]=fft_in[0][i]-10000;
                }
            }



            for(int i=0;i<sar_look_num;i++)
            {
                fft_in[0][i]-=mean;
            }
            fftw_plan p = FFTW3_H::fftw_plan_dft_r2c_1d(zero_time*sar_look_num, fft_in[0], fft_out[0], FFTW_ESTIMATE);

#else
            for(int i=0;i<sar_look_num;i++)
            {
                fft_in[0][i][0]=sar_data[0][i];
                fft_in[0][i][1]=sar_data[1][i];
            }
            fftw_plan p = fftw_plan_dft_1d(sar_look_num,fft_in[0],fft_out[0],FFTW_FORWARD, FFTW_ESTIMATE);


#endif

                fftw_execute(p);



                this->update();
                fps++;
            }

            //tcpsocket->write(QString("start").toLocal8Bit());
            //tcpsocket->flush();


        }
    }


}

void MainWindow::on_btn_start_clicked()
{
    if(rec_sta==0)
    {
        if(tcpsocket!=NULL)
        {
            rec_sta=1;
            ui->btn_start->setText("提前结束");
            rec_cnt=0;
            file_open();
            if(look_sta==0)
            {
                tcpsocket->write(QString("start").toLocal8Bit());
            }



        }

    }
    else
    {
        rec_sta=0;
        ui->btn_start->setText("开始");
        file_close();
        if(look_sta==0)
        {
             tcpsocket->write(QString("stop").toLocal8Bit());
        }
        rec_cnt=0;
    }
}
void MainWindow::file_open(void)
{
    file_idx++;
    now_file=data_file(QString("sar_%1.bin").arg(file_idx));
    ui->file_idx->setText(QString("上一个文件：%1").arg(file_idx));
    sar_file=new QFile(now_file);

    sar_file->open(QIODevice::WriteOnly | QIODevice::Truncate);


}
void MainWindow::file_write(QByteArray dat)
{
    sar_file->write(dat);
}
void MainWindow::file_close(void)
{
    sar_file->close();
    qDebug()<<"recorded"<<now_file;
}


void MainWindow::on_pushButton_clicked()
{
    if(look_sta==0)
    {
        look_sta=1;
        if(rec_sta==0)
        {
            tcpsocket->write(QString("start").toLocal8Bit());
        }

        ui->pushButton->setText("停止观测");
    }
    else
    {
        look_sta=0;
        if(rec_sta==0)
        {
            tcpsocket->write(QString("stop").toLocal8Bit());
        }

        ui->pushButton->setText("开始观测");
    }

}

void MainWindow::on_bp_start_clicked()
{
    if(now_file=="")return;
    sar_data_cleaner1->set_input_file(now_file);
    sar_data_cleaner1->set_output_file(clean_file_path);
    sar_data_cleaner1->start();

}
void MainWindow::clean_finish(QString file_name)
{
    sar_bp_1d_1->set_file(file_name);
}

void MainWindow::on_img_start_clicked()
{
    sar_bp_1d_1->set_noise_clean_file(runtime_config.noise_file);
    sar_bp_1d_1->set_dir(0);
    sar_bp_1d_1->set_geo(runtime_config.img_x, runtime_config.img_y, runtime_config.img_w, runtime_config.img_h);
    sar_bp_1d_1->set_grid(runtime_config.grid_x, runtime_config.grid_y);
    sar_bp_1d_1->set_sar_high(runtime_config.sar_height);

    sar_bp_1d_1->set_speed(runtime_config.speed);
    sar_bp_1d_1->start();
}
void MainWindow::get_img(QImage res,QImage dist_img)
{
    ui->label_2->setPixmap(QPixmap::fromImage(res));
    ui->label_3->setPixmap(QPixmap::fromImage(dist_img));
}

void MainWindow::on_horizontalSlider_sliderReleased()
{
    qDebug()<<ui->horizontalSlider->value();
    ui->label_2->setPixmap(QPixmap::fromImage(sar_bp_1d_1->get_res_at_level((double)(ui->horizontalSlider->value()))));
}
void MainWindow::set_noise_clean_file(QString file)
{
    QFile *in_file=new QFile();
    in_file->setFileName(file);
    if(in_file->open(QIODevice::ReadOnly)==0)
    {
        return;
    }
    char* read_buf=new char[sizeof (int)];
    in_file->read(read_buf,sizeof (int));
    int trip_len=*((int*)read_buf);
    delete [] read_buf;
    if(sar_noise!=NULL)
    {
        delete [] sar_noise;
    }
    sar_noise=new uint16_t[trip_len];
    quint64 now_pt;
    in_file->read((char*)(&now_pt),sizeof (quint64));
    in_file->read((char*)sar_noise,2*trip_len);
    in_file->close();
    sar_noise_len=trip_len;
    qDebug("获取噪声完成");
}

QString MainWindow::data_file(const QString &file_name) const
{
    return runtime_config.data_file(file_name);
}

void MainWindow::on_file_idx_clicked()
{
    if(file_idx>0)
    {
        file_idx--;
        ui->file_idx->setText(QString("上一个文件：%1").arg(file_idx));
    }
}

void MainWindow::on_set_file_idx_clicked()
{
    bool bOk;
    int t_idx = QInputDialog::getInt(this,
                                    "请输入上一个文件idx",
                                    "请输入上一个文件idx",
                                    1,				//默认值
                                    1,				//最小值
                                    1000,			//最大值
                                    1,				//步进
                                    &bOk);
    file_idx=t_idx;
    ui->file_idx->setText(QString("上一个文件：%1").arg(file_idx));

}
