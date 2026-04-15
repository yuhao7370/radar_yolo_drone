#ifndef SAR_DATA_CLEANER_H
#define SAR_DATA_CLEANER_H

#include <QObject>
#include <QThread>
#include <QDebug>
#include <QString>
#include <QFile>


//此类用于清洗雷达采样数据
//确定数据的
class sar_data_cleaner :public QThread
{
    Q_OBJECT
public:
    void run(void) override;
    QString input_file;
    QString output_file;
    sar_data_cleaner();
    void set_input_file(QString file_path);
    void set_output_file(QString file_path);
    int is_times(quint64 exp,quint64 real);
    bool busy;

signals:
    void clean_finish(QString file_name);

};

#endif // SAR_DATA_CLEANER_H
