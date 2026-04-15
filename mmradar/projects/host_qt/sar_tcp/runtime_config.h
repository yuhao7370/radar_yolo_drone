#ifndef RUNTIME_CONFIG_H
#define RUNTIME_CONFIG_H

#include <QString>
#include <QtGlobal>

struct RuntimeConfig
{
    QString project_root;
    QString ini_path;
    QString data_dir;
    QString noise_file;
    quint16 listen_port;
    qulonglong target_size_kb;
    double img_x;
    double img_y;
    double img_w;
    double img_h;
    int grid_x;
    int grid_y;
    double speed;
    double sar_height;
    double contrast_level;
    bool fusion_export_enabled;
    QString fusion_output_dir;
    QString fusion_session_id;
    int fusion_snapshot_stride_trip;
    bool fusion_save_final_res;
    bool loaded_from_file;

    RuntimeConfig();

    static RuntimeConfig load();
    static QString find_project_root();

    QString data_file(const QString &file_name) const;
    QString fusion_session_root() const;
    QString fusion_radar_dir() const;
};

#endif // RUNTIME_CONFIG_H
