#include "runtime_config.h"

#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QSettings>
#include <QStringList>
#include <QDebug>

namespace {

QString resolve_from_root(const QString &root, const QString &path)
{
    if (QDir::isAbsolutePath(path)) {
        return QDir::cleanPath(path);
    }
    return QDir::cleanPath(QDir(root).filePath(path));
}

QString find_root_from(const QString &start_dir)
{
    QDir dir(start_dir);
    while (dir.exists()) {
        if (QFileInfo::exists(dir.filePath("PROJECT_BASELINE.md"))) {
            return dir.absolutePath();
        }
        if (!dir.cdUp()) {
            break;
        }
    }
    return QString();
}

}

RuntimeConfig::RuntimeConfig()
    : listen_port(2829)
    , target_size_kb(75000)
    , img_x(-2.0)
    , img_y(2.5)
    , img_w(5.0)
    , img_h(8.0)
    , grid_x(500)
    , grid_y(800)
    , speed(0.12)
    , sar_height(0.872)
    , contrast_level(6764.0)
    , loaded_from_file(false)
{
}

RuntimeConfig RuntimeConfig::load()
{
    RuntimeConfig config;
    config.project_root = find_project_root();
    if (config.project_root.isEmpty()) {
        config.project_root = QDir::currentPath();
        qWarning() << "未找到包含 PROJECT_BASELINE.md 的 mmradar 根目录，回退到当前目录:" << config.project_root;
    }

    config.ini_path = QDir(config.project_root).filePath("config/sar_tcp.ini");
    config.data_dir = resolve_from_root(config.project_root, "resources/data");
    config.noise_file = resolve_from_root(config.project_root, "resources/calibration/sar_noise_500M.bin");

    if (!QFileInfo::exists(config.ini_path)) {
        qWarning() << "未找到运行配置文件，使用内置默认值:" << config.ini_path;
        return config;
    }

    QSettings settings(config.ini_path, QSettings::IniFormat);
    config.loaded_from_file = true;

    config.data_dir = resolve_from_root(
        config.project_root,
        settings.value("paths/data_dir", "resources/data").toString()
    );
    config.noise_file = resolve_from_root(
        config.project_root,
        settings.value("paths/noise_file", "resources/calibration/sar_noise_500M.bin").toString()
    );
    config.listen_port = settings.value("network/listen_port", config.listen_port).toUInt();
    config.target_size_kb = settings.value("capture/target_size_kb", config.target_size_kb).toULongLong();
    config.img_x = settings.value("imaging/x", config.img_x).toDouble();
    config.img_y = settings.value("imaging/y", config.img_y).toDouble();
    config.img_w = settings.value("imaging/w", config.img_w).toDouble();
    config.img_h = settings.value("imaging/h", config.img_h).toDouble();
    config.grid_x = settings.value("imaging/grid_x", config.grid_x).toInt();
    config.grid_y = settings.value("imaging/grid_y", config.grid_y).toInt();
    config.speed = settings.value("imaging/speed", config.speed).toDouble();
    config.sar_height = settings.value("imaging/sar_height", config.sar_height).toDouble();
    config.contrast_level = settings.value("imaging/contrast_level", config.contrast_level).toDouble();
    return config;
}

QString RuntimeConfig::find_project_root()
{
    const QStringList start_dirs = {
        QCoreApplication::applicationDirPath(),
        QDir::currentPath()
    };

    for (const QString &start_dir : start_dirs) {
        const QString root = find_root_from(start_dir);
        if (!root.isEmpty()) {
            return root;
        }
    }

    return QString();
}

QString RuntimeConfig::data_file(const QString &file_name) const
{
    return QDir(data_dir).filePath(file_name);
}
