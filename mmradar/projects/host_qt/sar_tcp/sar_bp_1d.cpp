#include "sar_bp_1d.h"

#include <QDir>
#include <QFileInfo>

sar_bp_1d::sar_bp_1d()
{
    m_x=0;
    m_y=0;
    m_w=0;
    m_h=0;
    m_x_num=0;
    m_y_num=0;
    m_dir=0;
    m_name="";
    m_speed=0;
    trip_num=0;
    trip_len=0;
    zero_times=10;
    sar_noise=NULL;
    sar_noise_len=0;
    img=NULL;
    sar_high=-1;
    m_res_name="res.jpg";
    busy=0;
}
void sar_bp_1d::set_geo(double x,double y,double w,double h)//单位：米
{
    m_x=x;
    m_y=y;
    m_w=w;
    m_h=h;
}
void sar_bp_1d::set_grid(int x_num,int y_num)
{
    m_x_num=x_num;
    m_y_num=y_num;
}
void sar_bp_1d::set_dir(bool dir)//0:right,1:left
{
    m_dir=dir;
}
void sar_bp_1d::set_file(QString name)
{
    m_name=name;

}
void sar_bp_1d::set_speed(double speed)//单位：m/s
{
    m_speed=speed;
}
void sar_bp_1d::run(void)
{
    busy=1;
    qDebug()<<"开始成像";
    QFile *in_file=new QFile();
    in_file->setFileName(m_name);
    in_file->open(QIODevice::ReadOnly);
    quint64 file_len=in_file->size();
    char* read_buf=new char[sizeof (int)];
    in_file->read(read_buf,sizeof (int));
    trip_len=*((int*)read_buf);
    delete [] read_buf;
    int read_buf_len_in_byte=sizeof (quint64)+2*trip_len;
    trip_num=(file_len-sizeof (int))/ read_buf_len_in_byte/4;
    img=new std::complex<double>* [m_x_num];
    for(int i=0;i<m_x_num;i++)
    {
        img[i]=new std::complex<double> [m_y_num];
        for(int j=0;j<m_y_num;j++)
        {
            img[i][j].real(0);
            img[i][j].imag(0);
        }
    }
    int gap_h=15;
    int gap_t=50;
    int valid_trip_len=trip_len-gap_h-gap_t;

    double* fft_in=(double*)fftw_malloc(sizeof(double) * valid_trip_len*zero_times);
    fftw_complex* fft_out=(fftw_complex*)fftw_malloc(sizeof(fftw_complex) * valid_trip_len*zero_times);

    for(int i=0;i<valid_trip_len*zero_times;i++)
    {
        fft_in[i]=0;
    }

    uint16_t *sar_data=new uint16_t[trip_len];
    quint64 now_pt;
    double sar_pos_x=0;
    double sar_pos_y=0;
    double grid_pos_x=0;
    double grid_pos_y=0;
    double distance=0;
    double grid_w_half=m_w/m_x_num/2;
    double grid_h_half=m_h/m_y_num/2;
    double ramp_k=1.666259766e11;
    double c=3e8;
    double fs=1e6;
    double deta_f=fs/valid_trip_len/zero_times;
    int freq_idx=0;
    double freq_err=0;
    double pi=3.1415926535897932384;
    //double f=24e9+125e6;
    double f=24e9;
    uint32_t freq=0;
    std::complex<double> tmp_cplx;
    uint32_t round=0;
    double deta_p=0;
    std::complex<double> i1(0,1);
    std::complex<double> pa_err;//相位因子
    QImage res(m_x_num,m_y_num,QImage::Format_RGB888);


    QImage dist_img(1000,trip_num,QImage::Format_RGB888);
    fftw_plan p;

    int color=0;
    for(int j=0;j<1000;j++)
    {
        color=255;
        for(int k=0;k<trip_num;k++)
        {
            dist_img.setPixelColor(j,k,QColor(color,color,color));
        }


    }


//    in_file->read((char*)(&now_pt),sizeof (quint64));
//    in_file->read((char*)sar_data,2*trip_len);
//    in_file->seek(sizeof (int));

    for(int i=0;i<trip_num;i++)
    {
        in_file->read((char*)(&now_pt),sizeof (quint64));
        in_file->read((char*)sar_data,2*trip_len);
        in_file->skip(3*read_buf_len_in_byte);

//        in_file->read((char*)(&now_pt),sizeof (quint64));
//        in_file->skip(4*read_buf_len_in_byte-sizeof (quint64));

        qDebug()<<"成像进度"<<i<<"/"<<trip_num;

        static int cnt=0;
        if(cnt++%10==9)
        {
            cnt=0;
            static int tmp_cnt=0;
            const QFileInfo res_info(m_res_name);
            const QString progress_dir = res_info.absolutePath();
            if(!progress_dir.isEmpty())
            {
                res.mirrored(1,1).save(QDir(progress_dir).filePath(QString("progress_%1.jpg").arg(tmp_cnt)));
            }
            tmp_cnt++;
        }
        else
        {
            continue;
        }


        sar_pos_x=((m_speed*now_pt)/1000000);


        uint16_t mean=0;
        uint64_t sum=0;
        for(int i=0;i<valid_trip_len;i++)
        {
            fft_in[i]=sar_data[gap_h+i];
            sum+=sar_data[gap_h+i];
        }
        mean=sum/valid_trip_len;
        if(sar_noise==NULL)
        {
            for(int i=0;i<valid_trip_len;i++)
            {
                fft_in[i]-=mean;
            }
        }
        else
        {
            for(int i=0;i<valid_trip_len;i++)
            {
                if(gap_h+i<sar_noise_len)
                {
                   fft_in[i]-=sar_noise[gap_h+i];
                }
                else
                {
                    fft_in[i]-=mean;

                }
            }
        }

        //加窗
        for(int i=0;i<valid_trip_len;i++)
        {

           fft_in[i]=fft_in[i]*window(4,valid_trip_len,i);//汉宁窗
        }


        p = FFTW3_H::fftw_plan_dft_r2c_1d(valid_trip_len*zero_times, fft_in, fft_out, FFTW_ESTIMATE);
        fftw_execute(p);

        for(int j=0;j<200;j++)
        {
            color=sqrt(fft_out[j][0]*fft_out[j][0]+fft_out[j][1]*fft_out[j][1])*5/valid_trip_len;
            if(color>255)
            {
                color=255;
            }
            else if(color<0)
            {
                color=0;
            }
            for(int k=0;k<5;k++)
            {
                dist_img.setPixelColor(5*j+k,i,QColor(color,color,color));
            }


        }


        for(int x=0;x<m_x_num;x++)
        {
            for(int y=0;y<m_y_num;y++)
            {
                grid_pos_x=m_x+grid_w_half+m_w*x/m_x_num;
                grid_pos_y=m_y+grid_h_half+m_h*y/m_y_num;
                if(sar_high<0)
                {
                    distance=sqrt(pow(grid_pos_x-sar_pos_x,2)+pow(grid_pos_y-sar_pos_y,2));
                }
                else
                {
                    distance=sqrt(pow(grid_pos_x-sar_pos_x,2)+pow(grid_pos_y-sar_pos_y,2)+pow(sar_high,2));
                }
                freq=2*distance*ramp_k/c;
                freq_idx=freq/deta_f;
                freq_err=(freq/deta_f)-freq_idx;

                tmp_cplx.real((1-freq_err)*fft_out[freq_idx][0]+freq_err*fft_out[freq_idx+1][0]);
                tmp_cplx.imag((1-freq_err)*fft_out[freq_idx][1]+freq_err*fft_out[freq_idx+1][1]);

//                tmp_cplx*=pow(distance/100,1);
//                if(abs(tmp_cplx)<100)
//                {
//                    continue;
//                }
                round=distance*f/c*2;
                deta_p=(distance*f/c*2-round)*2*pi;

                //pa_err.real(cos(deta_p));
                //pa_err.imag(sin(deta_p));
                //img[x][y]+=tmp_cplx/pa_err;
                //qDebug()<<round<<(distance*f/c*2-round)<<deta_p<<distance;

                img[x][y]+=tmp_cplx/std::exp(i1*deta_p);

                //img[x][y]+=abs(tmp_cplx)*pow(distance/100,1);
            }
        }



        double max=0;
        for(int x=0;x<m_x_num;x++)
        {
            for(int y=0;y<m_y_num;y++)
            {
                if(max<abs(img[x][y]))
                {
                    max=abs(img[x][y]);
                }
            }

        }
        if(max!=0)
        {
            for(int x=0;x<m_x_num;x++)
            {
                for(int y=0;y<m_y_num;y++)
                {
                    color=abs(img[x][y])/max*255*2;
                    if(color>255)
                    {
                        color=255;
                    }
                    res.setPixelColor(x,y,QColor(color,color,color));

                }
            }
            emit get_img(res.mirrored(1,1),dist_img);
        }



    }

    qDebug()<<"成像结束";

    double max=0;
    for(int x=0;x<m_x_num;x++)
    {
        for(int y=0;y<m_y_num;y++)
        {
            if(max<abs(img[x][y]))
            {
                max=abs(img[x][y]);
            }
        }

    }
    for(int x=0;x<m_x_num;x++)
    {
        for(int y=0;y<m_y_num;y++)
        {

            color=abs(img[x][y])*255/max*2;
            if(color>255)
            {
                color=255;
            }
            res.setPixelColor(x,y,QColor(color,color,color));

        }
    }
    res=res.mirrored(1,1);
    emit get_img(res,dist_img);
    busy=0;


}
void sar_bp_1d::set_noise_clean_file(QString file)
{

    QFile *in_file=new QFile();
    in_file->setFileName(file);
    in_file->open(QIODevice::ReadOnly);
    quint64 file_len=in_file->size();
    char* read_buf=new char[sizeof (int)];
    in_file->read(read_buf,sizeof (int));
    int trip_len=*((int*)read_buf);
    delete [] read_buf;
    int read_buf_len_in_byte=sizeof (quint64)+2*trip_len;
    trip_num=(file_len-sizeof (int))/ read_buf_len_in_byte/4;
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
void sar_bp_1d::set_res_name(QString res_name)//设置成像结果存储路径+文件名
{
    m_res_name=res_name;
}
QImage sar_bp_1d::get_res_at_level(double level)
{
    busy=1;
    double max=0;
    int color=0;
    QImage res(m_x_num,m_y_num,QImage::Format_RGB888);
    if(img==NULL)
    {
        return res;
    }
    for(int x=0;x<m_x_num;x++)
    {
        for(int y=0;y<m_y_num;y++)
        {
            if(max<abs(img[x][y]))
            {
                max=abs(img[x][y]);
            }
        }

    }
    double org_color=0;
    for(int x=0;x<m_x_num;x++)
    {
        for(int y=0;y<m_y_num;y++)
        {
             org_color=abs(img[x][y]);
            if(org_color<200*level)
            {
                color=0;
            }
            else
            {
                color=(org_color-200*level)*255/max*6;
                if(color>255)
                {
                    color=255;
                }
            }

            res.setPixelColor(x,y,QColor(color,color,color));

        }
    }
    res=res.mirrored(1,1);
    qDebug()<<"结果保存在"<<m_res_name;
    busy=0;

    return res;
}
void sar_bp_1d::set_sar_high(double h)
{
    sar_high=h;
}
double sar_bp_1d::window(int type, int n, int i)//type：窗函数的类型   n：窗口长度  i：当前索引
{
    int k;
    double pi;
    double w;
    pi = 4.0 * atan(1.0);  //pi=PI;
    w = 1.0;
    switch (type)
    {
    case 1:
    {
        w = 1.0;  //矩形窗
        break;
    }
    case 2:
    {
        k = (n - 2) / 10;
        if (i <= k)
        {
            w = 0.5 * (1.0 - cos(i * pi / (k + 1)));  //图基窗
        }
        if (i > n-k-2)
        {
            w = 0.5 * (1.0 - cos((n - i - 1) * pi / (k + 1)));
        }
        break;
    }
    case 3:
    {
        w = 1.0 - fabs(1.0 - 2 * i / (n - 1.0));//三角窗
        break;
    }
    case 4:
    {
        w = 0.5 * (1.0 - cos( 2 * i * pi / (n - 1)));//汉宁窗
        break;
    }
    case 5:
    {
        w = 0.54 - 0.46 * cos(2 * i * pi / (n - 1));//海明窗
        break;
    }
    case 6:
    {
        w = 0.42 - 0.5 * cos(2 * i * pi / (n - 1)) + 0.08 * cos(4 * i * pi / (n - 1));//布莱克曼窗
        break;
    }
    }
    return(w);
}
