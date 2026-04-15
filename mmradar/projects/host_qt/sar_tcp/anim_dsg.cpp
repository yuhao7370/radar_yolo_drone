#include "anim_dsg.h"


anim_dsg::anim_dsg()
{
    this->resize(462,618);
    this->setWindowFlag(Qt::FramelessWindowHint);

    this->setAttribute(Qt::WA_TranslucentBackground,true);


    //this->setWindowOpacity(0.5);

//    QVector<float>res;
//    res.push_back(0);
//    res.push_back(0);
//    for(int i=0;i<10;i++)
//    {
//        res[0]=org[i][0];
//        res[1]=org[i][1];
//        res=cvt_point(res);
//        now_anim[i][0]=res[0]/6.6819;
//        now_anim[i][1]=res[1]/6.6819;
//    }

    now_step=0;

    set_step(now_step);

    this->show();




}
QVector<float> anim_dsg::cvt_point(QVector<float> src)
{
    float u = src[0];
    float v = src[1];
    QVector<float> dst;
    dst.push_back( (M[0*3+0]*u+M[0*3+1]*v+M[0*3+2])/(M[2*3+0]*u+M[2*3+1]*v+M[2*3+2]));
    dst.push_back((M[1*3+0]*u+M[1*3+1]*v+M[1*3+2])/(M[2*3+0]*u+M[2*3+1]*v+M[2*3+2]));
    return dst;

}
void anim_dsg::paintEvent(QPaintEvent *event)
{
    QPainter painter(this);
    painter.setPen(QPen(Qt::red,2));
    painter.setBrush(QColor(0,0,0,0));
    painter.drawRect(0,0,this->width(),this->height());
    for(int i=0;i<10;i++)
    {
        painter.drawEllipse(now_anim[i][0]-5,now_anim[i][1]-5,10,10);
    }
    painter.setFont(QFont("Arial", 30));
    painter.drawText(10,30,QString("当前step=%1").arg(now_step));

}
void anim_dsg::set_step(int step)//0-90
{
    int start_idx=step/30;
    int stop_idx=start_idx+1;
    float next_power=((float)(step-start_idx*30))/30;
    if(step<90)
    {
        for(int i=0;i<10;i++)
        {
            now_anim[i][0]=anim[start_idx][i][0]*(1-next_power)+anim[stop_idx][i][0]*next_power;
            now_anim[i][1]=anim[start_idx][i][1]*(1-next_power)+anim[stop_idx][i][1]*next_power;
        }
    }
    else
    {
        for(int i=0;i<10;i++)
        {
            now_anim[i][0]=anim[start_idx][i][0];
            now_anim[i][1]=anim[start_idx][i][1];
        }
    }

    QVector<float>res;
    res.push_back(0);
    res.push_back(0);
    for(int i=0;i<10;i++)
    {
        res[0]=now_anim[i][0];
        res[1]=now_anim[i][1];
        res=cvt_point(res);
        now_anim[i][0]=res[0]/6.6819;
        now_anim[i][1]=res[1]/6.6819;
    }
    this->update();
}
void anim_dsg::wheelEvent(QWheelEvent *event)    // 滚轮事件
{
    int val=event->angleDelta().y(); //delta()
    now_step+=val/abs(val);
    if(now_step>150)
    {
        now_step=150;
    }
    if(now_step<0)
    {
        now_step=0;
    }
    set_step(now_step);
}
