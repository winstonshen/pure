import sys, os
from PySide2.QtWidgets import QApplication, QWidget, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QSystemTrayIcon, QSlider, QMenu, QAction, QStackedWidget
from PySide2.QtGui import QPixmap, QIcon
from PySide2.QtCore import Qt, QUrl, Signal, QPoint
from PySide2.QtMultimedia import QMediaPlayer, QMediaPlaylist


SOUND_LIST = []
PATH_LIST = []
default_list = os.listdir('./sound/default/')
user_list = os.listdir('./sound/')
for file_name in default_list:
    if file_name[-4:] in ['.wav', '.mp3', '.wma', '.m4a']:
        SOUND_LIST.append(file_name)
        PATH_LIST.append('./sound/default/%s' % file_name)
for file_name in user_list:
    if file_name[-4:] in ['.wav', '.mp3', '.wma', '.m4a']:
        SOUND_LIST.append(file_name)
        PATH_LIST.append('./sound/%s' % file_name)
DEFAULT_COUNT = len(default_list)
SOUND_COUNT = len(PATH_LIST)

SHOW_HELP = True
config_file = open('./.config', 'r')
if config_file.readline()[8:9] == '1':
    SHOW_HELP = False
config_file.close()


class Player(QMediaPlayer):
    global PATH_LIST

    def __init__(self, parent=None):
        super().__init__(parent)
        self.play_list = QMediaPlaylist()
        self.play_list.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        for file_path in PATH_LIST:
            self.play_list.addMedia(QUrl.fromLocalFile(file_path))
        self.play_list.setCurrentIndex(0)

        self.setPlaylist(self.play_list)
        self.setVolume(65)


class HeartCheck(QLabel):
    checked_signal = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_checked = False
        self.setPixmap(QPixmap('./img/icon_hollow_16.png'))

    def mouseReleaseEvent(self, event):
        if self.is_checked:
            self.setPixmap(QPixmap('./img/icon_hollow_16.png'))
            self.is_checked = False
        else:
            self.setPixmap(QPixmap('./img/icon_16.png'))
            self.is_checked = True
        self.checked_signal.emit(self.is_checked)


class HelpNavigator(QLabel):
    next_signal = Signal(int)
    close_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = 0
        self.setPixmap(QPixmap('./img/right.png'))
        self.setFixedSize(25, 25)

    def mouseReleaseEvent(self, event):
        if self.current_index < 2:
            self.current_index += 1
            self.next_signal.emit(self.current_index)
        elif self.current_index < 3:
            self.setPixmap(QPixmap('./img/close.png'))
            self.current_index += 1
            self.next_signal.emit(self.current_index)
        else:
            self.close_signal.emit()


class TextDisplay(QStackedWidget):
    noticed_checked = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        welcome_text = '你好，我是清心。\n\n在专心写作、高效工作或者放空自己的时候，\n你可能会需要我。'
        guide_text = '如果需要我隐藏起来，或者暂时不需要我了，\n你可以双击或者中键单击系统托盘处我的图标让我隐藏或者退出。'
        personal_text = '对了，你也可以把自己喜欢的音频放在sound文件夹下。\n下次见面时，我就可以播放它们了。'
        end_text = '很高兴认识你。'

        self.welcome_label = QLabel(welcome_text, self)
        self.guide_label = QLabel(guide_text, self)
        self.personal_label = QLabel(personal_text, self)

        self.welcome_label.setWordWrap(True)
        self.welcome_label.setAlignment(Qt.AlignTop)
        self.guide_label.setWordWrap(True)
        self.guide_label.setAlignment(Qt.AlignTop)
        self.personal_label.setWordWrap(True)
        self.personal_label.setAlignment(Qt.AlignTop)

        self.end_frame = QFrame(self)
        self.end_label = QLabel(end_text, self.end_frame)
        self.noticed_check = HeartCheck(self.end_frame)
        self.noticed_label = QLabel('好的，我知道了。', self.end_frame)

        self.end_label.setAlignment(Qt.AlignCenter)

        end_hbox = QHBoxLayout()
        end_hbox.addWidget(self.noticed_check)
        end_hbox.addWidget(self.noticed_label)
        end_hbox.addStretch(1)
        end_hbox.setSpacing(10)

        end_vbox = QVBoxLayout()
        end_vbox.addWidget(self.end_label)
        end_vbox.addSpacing(20)
        end_vbox.addLayout(end_hbox)

        self.end_frame.setLayout(end_vbox)

        self.addWidget(self.welcome_label)
        self.addWidget(self.guide_label)
        self.addWidget(self.personal_label)
        self.addWidget(self.end_frame)

        self.noticed_check.checked_signal.connect(self.noticed_checked)


class HelpPad(QWidget):
    help_qss = '''
        QFrame{
            background-color: rgb(242, 244, 246);
            font: rgb(51, 51, 51);
            font-family: SimHei;
            font-size: 16px;}
        TextDisplay{
            margin-left: 10px;
            margin-right: 8px;}
        QFrame#top_bar{
            background-color: rgb(11, 162, 154);
            border-bottom: 1px solid gray;}
            '''

    def __init__(self, application: QApplication):
        super().__init__()

        self.app = application
        width = self.app.desktop().availableGeometry().width()
        height = self.app.desktop().availableGeometry().height()
        self.move(width - 210, height - 255)

        self.noticed = False

        self.setFixedSize(180, 180)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.central_frame = QFrame(self)
        self.central_frame.setFixedSize(180, 180)

        self.top_bar = QFrame(self.central_frame)
        self.top_bar.setObjectName('top_bar')
        self.top_bar.setFixedSize(180, 15)

        self.text_display = TextDisplay(self.central_frame)

        self.navigator = HelpNavigator(self.central_frame)

        self.navigator.next_signal.connect(self.text_display.setCurrentIndex)
        self.navigator.close_signal.connect(self.close)
        self.text_display.noticed_checked.connect(self.noticed_check)

        navi_box = QHBoxLayout()
        navi_box.addStretch(1)
        navi_box.addWidget(self.navigator)
        navi_box.addStretch(1)

        main_box = QVBoxLayout()
        main_box.addWidget(self.top_bar)
        main_box.addSpacing(15)
        main_box.addWidget(self.text_display)
        main_box.addSpacing(5)
        main_box.addLayout(navi_box)
        main_box.addSpacing(15)
        main_box.setStretch(1, 1)
        main_box.setSpacing(0)
        main_box.setContentsMargins(0, 0, 0, 0)

        self.central_frame.setLayout(main_box)

        self.setStyleSheet(self.help_qss)

    def noticed_check(self, is_checked: bool):
        self.noticed = is_checked

    def closeEvent(self, event):
        if self.noticed:
            config_file = open('./.config', 'w')
            config_file.write('noticed:1')
            config_file.close()


class PlayButton(QLabel):
    play_signal = Signal()
    pause_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap('./img/pause.png'))
        self.setFixedSize(30, 50)
        self.is_playing = True

    def mousePressEvent(self, event):
        if self.is_playing:
            self.setPixmap(QPixmap('./img/pause_pressed.png'))
        else:
            self.setPixmap(QPixmap('./img/play_pressed.png'))

    def mouseReleaseEvent(self, event):
        if self.is_playing:
            self.setPixmap(QPixmap('./img/play.png'))
            self.pause_signal.emit()
            self.is_playing = False
        else:
            self.setPixmap(QPixmap('./img/pause.png'))
            self.play_signal.emit()
            self.is_playing = True


class NaviButton(QLabel):
    next_signal = Signal()
    previous_signal = Signal()

    def __init__(self, navi_type: str, parent=None):
        super().__init__(parent)
        self.navi_type = navi_type
        if self.navi_type == 'previous':
            self.setPixmap(QPixmap('./img/previous.png'))
        elif self.navi_type == 'next':
            self.setPixmap(QPixmap('./img/next.png'))
        self.setFixedSize(30, 50)

    def mousePressEvent(self, event):
        if self.navi_type == 'previous':
            self.setPixmap(QPixmap('./img/previous_pressed.png'))
        elif self.navi_type == 'next':
            self.setPixmap(QPixmap('./img/next_pressed.png'))

    def mouseReleaseEvent(self, event):
        if self.navi_type == 'previous':
            self.setPixmap(QPixmap('./img/previous.png'))
            self.previous_signal.emit()
        elif self.navi_type == 'next':
            self.setPixmap(QPixmap('./img/next.png'))
            self.next_signal.emit()


class VolumeButton(QLabel):
    button_pressed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap('./img/option_bar.png'))
        self.setFixedSize(15, 50)
        self.volume_show = False

    def mouseReleaseEvent(self, event):
        self.button_pressed.emit(self.volume_show)
        if self.volume_show:
            self.volume_show = False
        else:
            self.volume_show = True


class ButtonFrame(QFrame):
    global SOUND_COUNT
    play_signal = Signal()
    pause_signal = Signal()
    next_signal = Signal(int)
    previous_signal = Signal(int)
    leave_signal = Signal()
    volume_pressed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = 0

        self.play_button = PlayButton(self)
        self.previous_button = NaviButton('previous', self)
        self.next_button = NaviButton('next', self)
        self.volume_button = VolumeButton(self)

        self.play_button.pause_signal.connect(self.pause_signal)
        self.play_button.play_signal.connect(self.play_signal)
        self.previous_button.previous_signal.connect(self.previous)
        self.next_button.next_signal.connect(self.next)
        self.volume_button.button_pressed.connect(self.volume_pressed)

        main_box = QHBoxLayout()
        main_box.addWidget(self.previous_button)
        main_box.addWidget(self.play_button)
        main_box.addWidget(self.next_button)
        main_box.addWidget(self.volume_button)
        main_box.setContentsMargins(0, 0, 0, 0)
        main_box.setSpacing(0)
        self.setLayout(main_box)
        self.setFixedSize(105, 50)

    def next(self):
        if self.current_index < SOUND_COUNT - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        self.next_signal.emit(self.current_index)

    def previous(self):
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = SOUND_COUNT - 1
        self.previous_signal.emit(self.current_index)

    def leaveEvent(self, event):
        self.leave_signal.emit()


class DisplayArea(QLabel):
    global DEFAULT_COUNT
    enter_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap('./img/flame.png'))
        self.setFixedSize(105, 50)

    def change_pic(self, index):
        if index < DEFAULT_COUNT:
            self.setPixmap(QPixmap('./img/%s.png' % SOUND_LIST[index][:-4]))
        else:
            self.setPixmap(QPixmap('./img/display.png'))

    def enterEvent(self, event):
        self.enter_signal.emit()


class DragBar(QLabel):

    move_signal = Signal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_moving = False
        self.setPixmap(QPixmap('./img/drag_bar.png'))
        self.setFixedSize(15, 50)
        self.start_point = self.parent().frameGeometry().topLeft()

    def mousePressEvent(self, event):
        self.is_moving = True
        self.start_point = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.is_moving = False

    def mouseMoveEvent(self, event):
        if self.is_moving:
            new_point = event.globalPos()
            move_distance = new_point - self.start_point
            self.move_signal.emit(move_distance)
            self.start_point = new_point


class VolumeControl(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOrientation(Qt.Horizontal)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(65)
        self.setFixedSize(120, 7)


class TrayMenu(QMenu):
    action_pressed = Signal(str)

    def __init__(self):
        super().__init__()
        self.addAction('帮助')
        self.addSeparator()
        self.addAction('隐藏/显示')
        self.addSeparator()
        self.addAction('退出')
        self.triggered.connect(self.send_action)

    def send_action(self, action: QAction):
        action_text = action.text()
        self.action_pressed.emit(action_text)


class TrayIcon(QSystemTrayIcon):
    show_signal = Signal()
    hide_signal = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent = parent
        self.tray_menu = TrayMenu()
        self.setContextMenu(self.tray_menu)
        self.is_show = True
        self.activated.connect(self.show_hide_close)
        self.tray_menu.action_pressed.connect(self.show_hide_close)

    def show_hide_close(self, reason):
        if reason == QSystemTrayIcon.DoubleClick or reason == '隐藏/显示':
            if self.parent.isVisible():
                self.parent.hide()
            else:
                self.parent.show()
        elif reason == QSystemTrayIcon.MiddleClick or reason == '退出':
            self.parent.app.exit(0)
        elif reason == '帮助':
            os.startfile('%s/help.pdf' % os.getcwd())


class MainWindow(QWidget):
    main_qss = '''QWidget {
        margin: 0px;
        padding: 0px;
        border: 0px;}
        QSlider {
            background-color: rgb(25, 38, 58);
            max-width: 120px;
            min-width: 120px;
            max-height: 8px;
            min-height: 8px;
            border: 0px;
            border-top: 1px solid rgb(51, 51, 51);
            margin: 0px;
            padding: 0px;}
        QSlider::handle:horizontal{
            background-color: rgb(51, 51, 51);
            border-radius: 2px;
            }
        QSlider::sub-page:horizontal{
            height: 8px;
            background-color: rgb(37, 168, 198);}
        QSlider::add-page:horizontal{
            height: 8px;
            background-color: rgb(171, 183, 183);}
        QMenu{
            font-family: SimHei;}
            '''

    def __init__(self, application: QApplication):
        super().__init__()
        self.app = application
        width = self.app.desktop().availableGeometry().width()
        height = self.app.desktop().availableGeometry().height()
        self.move(width - 150, height - 70)
        self.top_left_point = self.frameGeometry().topLeft()
        self.player = Player(self)
        self.play_list = self.player.play_list
        self.drag_bar = DragBar(self)
        self.button_frame = ButtonFrame(self)
        self.display_area = DisplayArea(self)
        self.system_tray_icon = TrayIcon(self)
        self.volume_control = VolumeControl(self)

        self.system_tray_icon.setIcon(QIcon('./img/icon_16.png'))
        self.system_tray_icon.show()
        self.system_tray_icon.setToolTip('双击隐藏/显示\n中键退出程序')

        self.player.play()

        self.central_box = QHBoxLayout()
        self.central_box.addWidget(self.drag_bar)
        self.central_box.addWidget(self.display_area)
        self.central_box.addWidget(self.button_frame)
        self.central_box.setContentsMargins(0, 0, 0, 0)
        self.central_box.setSpacing(0)

        self.main_box = QVBoxLayout()
        self.main_box.addLayout(self.central_box)
        self.main_box.addWidget(self.volume_control)
        self.main_box.setContentsMargins(0, 0, 0, 0)
        self.main_box.setSpacing(0)
        self.setLayout(self.main_box)
        self.setStyleSheet(self.main_qss)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedSize(120, 50)
        self.setWindowTitle('小清心')
        self.setWindowIcon(QIcon('./img/icon_128.png'))

        self.button_frame.hide()
        self.button_frame.pause_signal.connect(self.player.pause)
        self.button_frame.play_signal.connect(self.player.play)
        self.button_frame.previous_signal.connect(self.play_list.setCurrentIndex)
        self.button_frame.next_signal.connect(self.play_list.setCurrentIndex)
        self.button_frame.leave_signal.connect(self.mouse_leave)
        self.button_frame.volume_pressed.connect(self.show_volume)

        self.display_area.enter_signal.connect(self.mouse_enter)

        self.drag_bar.move_signal.connect(self.drag_move)

        self.system_tray_icon.show_signal.connect(self.show)
        self.system_tray_icon.hide_signal.connect(self.hide)

        self.play_list.currentIndexChanged.connect(self.sound_changed)

        self.volume_control.hide()
        self.volume_control.valueChanged.connect(self.change_volume)

    def sound_changed(self, index):
        self.display_area.change_pic(index)

    def mouse_enter(self):
        self.display_area.hide()
        self.button_frame.show()

    def mouse_leave(self):
        self.button_frame.hide()
        self.display_area.show()

    def drag_move(self, distance: QPoint):
        new_top_left_point = self.top_left_point + distance
        self.move(new_top_left_point)
        self.top_left_point = new_top_left_point

    def change_volume(self, volume: int):
        self.player.setVolume(volume)

    def show_volume(self, option_open: bool):
        if option_open:
            self.volume_control.hide()
            self.setFixedSize(120, 50)
        else:
            self.volume_control.show()
            self.setFixedSize(120, 58)


if __name__ == '__main__':
    app = QApplication()
    main_window = MainWindow(app)
    main_window.show()
    if SHOW_HELP:
        help_pad = HelpPad(app)
        help_pad.show()
    sys.exit(app.exec_())
