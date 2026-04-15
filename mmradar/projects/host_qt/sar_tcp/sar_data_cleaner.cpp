#include "sar_data_cleaner.h"

sar_data_cleaner::sar_data_cleaner()
{
    input_file="";
    output_file="";
    busy=0;
}
void sar_data_cleaner::run(void)
{
    if(input_file=="")
    {
        qDebug()<<"input not set";
        return;
    }
    if(output_file=="")
    {
        qDebug()<<"output not set";
        return;
    }
    qDebug()<<"数据清洗开始!";
    busy=1;

    QFile* in_file=new QFile(input_file);
    in_file->open(QIODevice::ReadOnly);
    qint64 file_len=in_file->size();
    QByteArray bp_byteArray=in_file->readAll();
    uint16_t* bp_data=(uint16_t*)bp_byteArray.data();
    if(file_len==0)
    {
        qDebug()<<"警告！文件打开失败！";
        return;
    }
    qDebug()<<"文件大小="<<file_len<<"字节";
    if(file_len%2!=0)
    {
        qDebug()<<"警告！文件大小为奇数";
    }
    qint64 dot_cnt=file_len/2;


    //测量trip平均长度
    qint64 now_pt = 0;
    int mesur_trip_cnt=0;
    qint64 trip_len_sum=0;
    qint64 pre_trip_flag=0;
    bool pre_muxout=0;

    pre_muxout=(bp_data[now_pt]&0x0002)>>1;
    while(pre_muxout==((bp_data[now_pt]&0x0002)>>1))//将指针移动到最近一个trip开始,实验发现每次都卡在2a
    {
        now_pt++;
    }

    qint64 first_trip_pt=now_pt;
    pre_muxout=(bp_data[now_pt]&0x0002)>>1;
    pre_trip_flag=now_pt;
    while(now_pt<dot_cnt)
    {
        if(pre_muxout!=((bp_data[now_pt]&0x0002)>>1))
        {
             pre_muxout=(bp_data[now_pt]&0x0002)>>1;
            if(now_pt-pre_trip_flag>20)//间隔超过20才算一次真正的trip
            {
                trip_len_sum+=now_pt-pre_trip_flag;
                mesur_trip_cnt++;
                pre_trip_flag=now_pt;
            }
        }
        now_pt++;
    }
    int mesur_trip_len=trip_len_sum/mesur_trip_cnt/4;
    mesur_trip_len*=0.995;//补偿
    qDebug()<<"测量得到trip长度为"<<mesur_trip_len;


    //开始数据清洗
    QFile* out_file=new QFile(output_file);
    out_file->open(QIODevice::WriteOnly | QIODevice::Truncate);
    out_file->write((char*)(&mesur_trip_len),sizeof (int));//文件开头写入trip长度。



    bool stop=0;

    now_pt=first_trip_pt;
    int tmp_ch=1;//1、2、3、4分别代表1a,1b,2a,2b
    quint64 next_trip_pt=now_pt;


    uint16_t *sar_data=NULL;
    int valid_data_cnt=0;
    int muxout_loss=0;
    int samp_err=0;
    int samp_not_4=0;
    quint64 trip_num=0;

    while(stop==0)
    {
        next_trip_pt=now_pt;
        pre_muxout=(bp_data[next_trip_pt]&0x0002)>>1;
        while((pre_muxout==((bp_data[next_trip_pt]&0x0002)>>1)))//寻找下一个trip
        {
            next_trip_pt++;
            if(next_trip_pt>=dot_cnt-1)
            {
                stop=1;
                goto wash_end;
            }
        }
        int cnt=0;
        while((bp_data[now_pt+cnt]&0x0001)==0)
        {
            cnt++;
        }
        tmp_ch=4-cnt%4;

        int times_res=is_times(mesur_trip_len,(next_trip_pt-now_pt)/4);
        if(times_res==-1)
        {
            qDebug()<<"出错！"<<(next_trip_pt-now_pt)/4<<"与"<<mesur_trip_len<<"无明显倍数关系！目前位于第"<<trip_num<<"个trip";
            now_pt=next_trip_pt;
            continue;
            //return;
        }
        else if(times_res==0)
        {
            qDebug()<<"出错！"<<(next_trip_pt-now_pt)/4<<"相对于"<<mesur_trip_len<<"太小了！目前位于第"<<trip_num<<"个trip";
            now_pt=next_trip_pt;
            continue;
        }
        else
        {
            //sar_data=new uint16_t[mesur_trip_len*4];
            sar_data=new uint16_t[ (mesur_trip_len+(sizeof(quint64)/sizeof (uint16_t))) *4];
            for(int i=0;i<(mesur_trip_len+(sizeof(quint64)/sizeof (uint16_t)))*4;i++)
            {
                sar_data[i]=0;
            }
            valid_data_cnt=(mesur_trip_len*4>(next_trip_pt-now_pt))?((next_trip_pt-now_pt)):(mesur_trip_len*4);
            if(valid_data_cnt%4!=0)
            {
                //qDebug()<<"警告！trip数据点数不是4的倍数！";
                samp_not_4++;
            }

            //记录位置
            for(int i=1;i<=4;i++)
            {
                *((quint64*)(sar_data + (i-1)* (mesur_trip_len+ (sizeof(quint64)/sizeof (uint16_t)))))=now_pt/4;
            }

            for(int i=0;i<valid_data_cnt;i++)
            {
               //sar_data[ (tmp_ch-1)*mesur_trip_len + (i/4) ]=bp_data[now_pt+i]>>2;
               sar_data[ (tmp_ch-1)* (mesur_trip_len+ (sizeof(quint64)/sizeof (uint16_t)) ) + (i/4) + (sizeof(quint64)/sizeof (uint16_t))]=bp_data[now_pt+i]>>2;
               tmp_ch++;

               if((bp_data[now_pt+i]&0x0001)==1)
               {
                   tmp_ch=1;
               }
               if(tmp_ch>4)
               {
                   tmp_ch=1;
                   //qDebug()<<"警告！遇到采样点丢失错误！目前位置"<<i/4<<"/"<<mesur_trip_len;
                   samp_err++;
                   while(i<valid_data_cnt && ((bp_data[now_pt+i]&0x0001) != 1))
                   {
                       i++;
                   }
                   i=i-1;
                   tmp_ch=3;
               }
            }
            //out_file->write((char*)sar_data,mesur_trip_len*4*2);
            out_file->write((char*)sar_data, (mesur_trip_len+(sizeof(quint64)/sizeof (uint16_t))) *4*2);
            delete[] sar_data;
            sar_data=NULL;
            if(times_res==1)//最好情况
            {
                now_pt=next_trip_pt;
            }
            else
            {
                now_pt=now_pt+(next_trip_pt-now_pt)/times_res;
                //now_pt=now_pt+mesur_trip_len*4;

                muxout_loss+=times_res-1;
            }
        }
        trip_num++;





    }

wash_end:

    qDebug()<<"脉冲漏检"<<muxout_loss<<"个，已补齐";
    qDebug()<<"采样丢失次数："<<samp_err;
    qDebug()<<"采样点非四次数："<<samp_not_4;
    qDebug()<<"trip总数："<<trip_num;
    qDebug()<<"数据清洗结束";
    in_file->close();
    out_file->close();
    busy=0;
    emit clean_finish(output_file);


}
int sar_data_cleaner::is_times(quint64 exp,quint64 real)
{
    float res_f=(float)real/exp;
    int res_big=res_f;
    float res_small=res_f-res_big;
    if(abs(res_small-0.5)<0.2)
    {
        return -1;
    }
    else
    {
        return res_small<0.5?res_big:res_big+1;
    }

}
void sar_data_cleaner::set_input_file(QString file_path)
{
    input_file=file_path;
    qDebug()<<"cleaner set input"<<file_path;
}
void sar_data_cleaner::set_output_file(QString file_path)
{
    output_file=file_path;
}

