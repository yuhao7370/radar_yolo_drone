QT       += core gui network

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++11

# You can make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
    anim_dsg.cpp \
    main.cpp \
    mainwindow.cpp \
    sar_bp.cpp \
    sar_bp_1d.cpp \
    sar_data_cleaner.cpp

HEADERS += \
    anim_dsg.h \
    mainwindow.h \
    sar_bp.h \
    sar_bp_1d.h \
    sar_data_cleaner.h

FORMS += \
    mainwindow.ui

# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target

msvc {
QMAKE_CFLAGS += /utf-8
QMAKE_CXXFLAGS += /utf-8
}



INCLUDEPATH += $$PWD/fftw
DEPENDPATH += $$PWD/fftw




LIBS += -L$$PWD/fftw/ -llibfftw3-3


INCLUDEPATH += $$PWD/fftw
DEPENDPATH += $$PWD/fftw

win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $$PWD/fftw/liblibfftw3-3.a
else:win32:!win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $$PWD/fftw/libfftw3-3.lib
