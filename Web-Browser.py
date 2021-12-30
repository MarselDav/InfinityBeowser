import datetime
import sqlite3
import sys

import requests
from PyQt5 import QtWidgets
from PyQt5.Qt import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QColorDialog


def is_website_correct(url):  # проверка на корректность url
    try:
        request = requests.get(url)
        if request.status_code == 200:
            return 1
    except:
        return 0


class WebEnginePage(QWebEnginePage):  # при клике на ссылку она открывается в новой вкладке
    external_window = None

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        self.url = url
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            if not self.external_window:
                browser.new_tab(str(self.url).split("'")[1])
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)


class MainWindow(QMainWindow, QWebEngineView):  # главное окно браузера
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # создание главного окна браузера и его элементов
        self.connect_bd()
        self.browser_design()
        self.all_tabs = []
        self.setGeometry(500, 500, 500, 500)
        self.setWindowTitle("Browser")
        self.setStyleSheet(f"""background-color: {self.start_color};""")
        self.setWindowIcon(QIcon("icons/browser_icon.png"))
        self.setIconSize(QSize(50, 50))
        self.delete_promptings = False

        # self.start_url = "https://google.com"  # url начальной страницы
        self.start_url = "HomePage"

        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)

        self.toolbar = QToolBar("Navigation", self)
        self.toolbar.setStyleSheet("""
            QToolBar {
                border: 2px;
                padding: 10px 2px;
                max-width: 28px;
            }
            QToolBar::item {
                border: 2px;
                padding: 1px 4px;
                background: transparent;
                border-radius: 4px;
                height: 24px;
            }
            QToolBar::item:selected {
                background: #c2c2c2;
            }
            QToolBar::item:pressed {
                background: #c2c2c2;
            }
        """)
        self.toolbar.setAllowedAreas(Qt.TopToolBarArea)
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(22, 22))
        self.addToolBar(self.toolbar)

        self.go_back = QAction(QIcon("icons/go_back.png"), "go back", self)
        self.go_back.triggered.connect(self.go_back_page)
        self.toolbar.addAction(self.go_back)

        self.go_forward = QAction(QIcon("icons/go_forward.png"), "go forward", self)
        self.go_forward.triggered.connect(self.go_forward_page)
        self.toolbar.addAction(self.go_forward)

        self.restart_page = QAction(QIcon("icons/restart_page.png"), "restart page", self)
        self.restart_page.triggered.connect(self.restarting_page)
        self.toolbar.addAction(self.restart_page)

        self.home_page = QAction(QIcon("icons/home_page.png"), "home page", self)
        self.home_page.triggered.connect(self.goto_home_page)
        self.toolbar.addAction(self.home_page)

        self.search_bar = QLineEdit(self.start_url)
        self.search_bar.returnPressed.connect(self.url_navigate)
        self.search_bar.setStyleSheet("""
                    border: 1px;
                    border-radius: 10px;
                    background-color: white;
                    padding: 6;
                    font: 12px/14px sans-serif
                """)

        self.settings_bar = QMenuBar(self)
        self.settings_bar.setStyleSheet("""
            QMenuBar {
                border: 2px;
                padding: 10px 2px;
                max-width: 28px;
            }
            QMenuBar::item {
                border: 2px;
                padding: 1px 4px;
                background: transparent;
                border-radius: 4px;
                height: 24px;
            }
            QMenuBar::item:selected {
                background: #c2c2c2;
            }
            QMenuBar::item:pressed {
                background: #c2c2c2;
            }
        """)
        self.clear_url = QAction(QIcon("icons/clear_url.jpg"), "Clear url", self.search_bar)
        self.clear_url.triggered.connect(self.clear_search_bar)
        self.search_bar.addAction(self.clear_url, 1)
        self.settings = QMenu("Настройки", self)

        self.settings.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px;
                border-color: black;
                border-style: solid;
            }
            QMenu::item:selected {
                color: red;
            }
        """)

        self.settings.setIcon(QIcon('icons/settings.png'))

        self.newtab = QAction("Новая вкладка", self)
        self.newtab.triggered.connect(self.new_tab_doubelclick)
        self.settings.addAction(self.newtab)

        self.browser_settings = QAction("Настройки и управление", self)
        self.browser_settings.triggered.connect(self.settings_open)
        self.settings.addAction(self.browser_settings)

        self.settings_bar.addMenu(self.settings)
        self.toolbar.addWidget(self.search_bar)
        self.toolbar.addWidget(self.settings_bar)

        self.toolbar.setStyleSheet("""spacing: 5px;""")

        self.tabs = QTabWidget(self)
        self.tabs.setTabShape(int(self.tabs_shape))
        self.tabs_set_style_sheet()

        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.new_tab_doubelclick)
        self.tabs.tabBarClicked.connect(self.update_url)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setTabsClosable(True)

        if self.start_url == "HomePage":
            self.new_home_page_tab()
        else:
            self.new_tab(self.start_url)

        self.browser = QGridLayout(self.centralwidget)  # создаем сеточный макета
        self.browser.addWidget(self.toolbar)
        self.browser.addWidget(self.tabs)
        self.browser.setSpacing(10)

    def browser_design(self):  # загрузка дизайна из бд
        self.start_color = self.cursor.execute("""
        SELECT value FROM themes WHERE name = 'StartColor'""").fetchone()[0]
        self.tabs_shape = self.cursor.execute("""
        SELECT value FROM themes WHERE name = 'TabsShape'""").fetchone()[0]
        self.start_url = self.cursor.execute("""
        SELECT value FROM themes WHERE name = 'StartUrl'""").fetchone()[0]
        self.buttons_color = self.cursor.execute("""
        SELECT value FROM themes WHERE name = 'ButtonsColor'""").fetchone()[
            0]
        self.color_of_tabs = self.cursor.execute("""
        SELECT value FROM themes WHERE name = 'TabsColor'""").fetchone()[0]
        self.home_page_image = \
            self.cursor.execute("""
            SELECT value FROM themes WHERE name = 'HomePageImage'""").fetchone()[0]

        self.promptings = self.cursor.execute("""SELECT name, url, color FROM promptings""").fetchall()

    def url_navigate(self):  # перемещение по ссылкой вписанной в поисковую строку
        url = QUrl(self.search_bar.text())
        if url.scheme() == "":
            url = QUrl("http://www." + str(url).split("'")[1])
        if is_website_correct(str(url).split("'")[1]):
            self.tabs.currentWidget().setUrl(url)

    def update_url(self, index):  # обновить url поисковой строки
        if index != -1 and self.tabs.widget(index) not in self.findChildren(QScrollArea):
            self.url_change(self.tabs.widget(index).url())
        elif index != -1 and self.tabs.widget(index) in self.findChildren(QScrollArea):
            self.url_change("HomePage")

    def clear_search_bar(self):  # очистить поисковую строку
        self.search_bar.setText("")

    def go_back_page(self):  # вернуться на пердыдущую страницу
        self.web.back()

    def go_forward_page(self):  # перейти на следующую страницу
        self.web.forward()

    def restarting_page(self):  # перезагрузить страницу
        self.web.reload()

    def history_record(self, item):
        self.url_change(self.sender().url())

    def goto_home_page(self):  # вернуться на домашнюю страницу
        if self.tabs.currentWidget().objectName() != "HomePage":
            self.tabs.currentWidget().setUrl(QUrl("https://google.com"))

    def new_tab_doubelclick(self):  # создание вкладки двойным кликом
        if self.start_url == "HomePage":
            self.new_home_page_tab()
        else:
            self.new_tab(self.start_url)

    def tabs_set_style_sheet(self):  # применить дизайн вкладок
        self.tabs.setStyleSheet(f"""
                    QTabWidget::tab-bar {{
                        border: 1px solid gray;
                    }}
                    QTabBar::tab {{
                        background: {self.color_of_tabs};
                        color: white;
                        padding: 2px;
                        padding-left:50px;
                        padding-right:50px;
                    }}
                """)

    def new_tab(self, url):  # создать вкладку
        self.web = QWebEngineView()
        self.web.setPage(WebEnginePage(self))
        self.web.setUrl(QUrl(url))
        self.web.settings().setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        self.web.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        self.web.page().fullScreenRequested.connect(lambda request: request.accept())
        self.web.urlChanged.connect(self.history_record)
        self.web.titleChanged.connect(self.adjustTitle)
        self.tabs.addTab(self.web, self.web.title())
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
        self.all_tabs.append(self.web)

    def new_home_page_tab(self):  # создать вкладку домащней страницы
        self.home = QScrollArea()
        self.search_bar.setEnabled(False)
        self.homepage_set_stylesheet()
        self.tabs.addTab(self.home, "Домашняя страница")
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
        self.tabs.currentWidget().setObjectName("HomePage")
        self.widget = QWidget()
        # self.home.setCentralWidget(self.widget)

        self.layout2 = QGridLayout(self.widget)
        self.layout().setContentsMargins(30, 30, 30, 30)
        self.layout().setSpacing(30)
        self.home.setLayout(self.layout2)
        self.add_promt = QPushButton("Добавить")
        self.add_promt.setFont(QFont("sans-serif", 20))
        self.add_promt.clicked.connect(self.add_hint)
        self.layout2.addWidget(self.add_promt, 1, 0)
        self.y_position = 1
        self.x_position = 1
        self.all_tabs.append(self.home)
        self.promptings = self.cursor.execute("""SELECT name, url, color FROM promptings""").fetchall()

        self.upload_promtings()

    def upload_promtings(self):  # подгрузить все подсказки
        for i in self.promptings:
            self.button = QPushButton(i[0], self)
            self.button.setFont(QFont("sans-serif", 20))
            self.button.setObjectName(i[1])
            self.button.clicked.connect(self.promptings_function)
            if len(self.home.findChildren(QPushButton)) % 3 == 0:
                self.x_position = 0
                self.y_position += 1
            self.layout2.addWidget(self.button, self.y_position, self.x_position)
            self.x_position += 1
            self.button.setStyleSheet(f"""background-color: {i[2]}""")

    def add_hint(self):  # добавить подсказку
        self.link, ok1 = QInputDialog.getText(self, "Добавить подсказку", "Введите ссылку")
        q = QUrl(self.link)
        if q.scheme() == '':
            self.link = "https://www." + self.link
        if is_website_correct(self.link):
            self.name, ok2 = QInputDialog.getText(self, "Добавить подсказку", "Введите имя")
            self.link = self.link.replace(".ru", ".com")
            if not ok2 or self.name == '':
                self.name = self.link
            if ok1:
                color_get = QColorDialog().getColor()
                self.button = QPushButton(self.name)
                self.button.setFont(QFont("sans-serif", 20))
                self.button.setObjectName(self.link)
                self.button.clicked.connect(self.promptings_function)
                if len(self.home.findChildren(QPushButton)) % 3 == 0:
                    self.x_position = 0
                    self.y_position += 1
                self.layout2.addWidget(self.button, self.y_position, self.x_position)
                self.x_position += 1
                self.button.setStyleSheet(f"""background-color: {color_get.name()}""")
                self.cursor.execute(
                    f"""INSERT INTO promptings VALUES('{self.name}', '{self.link}', '{color_get.name()}')""")
                self.bd.commit()
        else:  # окно ошибки
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText('Неверная ссылка')
            msg.setWindowTitle("Error")
            msg.exec_()

    def add_new_tab(self):  # добавить новую вкладку
        browser.new_tab(self.sender().objectName())
        self.url_change(self.tabs.currentWidget().url())

    def promptings_function(self):  # выполняется при нажатии на подсказку
        print(self.delete_promptings)
        if self.delete_promptings:  # если включен режим удаления, удаляет подсказку
            self.cursor.execute(
                f"""DELETE FROM promptings WHERE name =
                 '{self.sender().text()}' AND url = '{self.sender().objectName()}'""")
            self.bd.commit()
            self.promptings = self.cursor.execute("""SELECT name, url, color FROM promptings""").fetchall()
            self.sender().close()
        else:  # иначе добавляет
            self.add_new_tab()

    def homepage_set_stylesheet(self):  # применить дизайн к домашней странице
        self.home.setStyleSheet(f"""
                                    QScrollArea {{
                                        background-image:url({self.home_page_image});
                                    }}
                                    QPushButton {{
                                        height: 150px;
                                    }}
                                """)

    def close_tab(self, i):  # закрыть вкладку
        if self.tabs.count() >= 2:
            self.tabs.widget(i).close()
            self.tabs.removeTab(i)
            del self.all_tabs[i]

    def url_change(self, url):  # изменение url у строки ввода ссылки
        if url == "HomePage":
            self.search_bar.setEnabled(False)
        else:
            url = str(url).split("'")[1]
            self.search_bar.setEnabled(True)
        self.search_bar.setText(url)
        self.search_bar.setCursorPosition(0)

    def insert_into_bd(self, url):  # добавить новый запрос в бд
        if self.sender().title() != url:
            d = datetime.datetime.now()
            self.cursor.execute(
                f"""INSERT INTO history VALUES
                ({self.count + 1}, "{self.sender().title()}", '{url}', '{str(datetime.datetime.now())}')""")
            self.bd.commit()
            history.restart_table()
            self.count += 1

    def adjustTitle(self):  # изменения название вкладки при переходе на другой сайт
        self.tabs.setTabText(self.all_tabs.index(self.sender()), self.sender().title())
        if (str(self.sender().url()).split("'")[1]).split("/")[3] == '':
            self.insert_into_bd(str(self.sender().url()).split("'")[1][:-1:])
        else:
            self.insert_into_bd(str(self.sender().url()).split("'")[1])
        # self.tabs.currentWidget().setWindowTitle(self.sender().title())

    def connect_bd(self):  # подключения к бд
        self.bd = sqlite3.connect("browser_bd.db")
        self.cursor = self.bd.cursor()
        try:
            self.count = self.cursor.execute("""SELECT COUNT(*) FROM history""").fetchone()[0]
        except sqlite3.OperationalError:  # если бд не найдена, создание новой
            self.cursor.execute("""CREATE TABLE history (id INTEGER PRIMARY KEY, name TEXT, url TEXT, time TEXT)""")
            self.cursor.execute("""CREATE TABLE themes (id INTEGER PRIMARY KEY, name TEXT, value TEXT)""")
            self.cursor.execute("""INSERT INTO themes VALUES (1, 'StartColor', '#d0d0d0'), (2, 'TabsColor', '#d0d0d0'),
             (3, 'TabsShape', '1'), (4, 'StartUrl', 'HomePage'),
              (5, 'ButtonsColor', '#d0d0d0'), (6, 'HomePageImage', '')""")
            self.cursor.execute("""CREATE TABLE promptings (name TEXT, url TEXT, color TEXT)""")
            self.cursor.execute("INSERT INTO promptings VALUES('Google', 'https://www.google.com', 'red')")
            self.bd.commit()

    def settings_open(self):  # открыть окно настроек и управления
        settings.show()


class SettingsWindow(QMainWindow):  # окно настроек и управления
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(200, 200, 500, 400)
        self.setWindowTitle("Настройки и управление")
        self.setWindowIcon(QIcon("icons/settings.png"))
        self.buttons_set_stylesheet()
        # self.setIconSize(QSize(50, 50))

        self.section1 = QLabel("Цвет браузера:", self)
        self.section1.move(5, 95)

        self.background_button = QPushButton("Поставить фото на фон", self)
        self.background_button.move(300, 100)
        self.background_button.adjustSize()
        self.background_button.clicked.connect(self.background_photo)

        self.set_button_color = QPushButton("Цвет кнопок", self)
        self.set_button_color.move(100, 100)
        self.set_button_color.adjustSize()
        self.set_button_color.clicked.connect(self.select_color)

        self.castomize = QPushButton("Цвет темы", self)
        self.castomize.move(200, 100)
        self.castomize.adjustSize()
        self.castomize.clicked.connect(self.select_color)

        self.section2 = QLabel("Дизайн вкладок:", self)
        self.section2.move(5, 200)

        self.radionbutton1 = QRadioButton("Shaped", self)
        self.radionbutton1.setChecked(int(browser.tabs_shape))
        self.radionbutton1.clicked.connect(self.tabs_design)
        self.radionbutton1.move(100, 200)

        self.radionbutton2 = QRadioButton("No Shaped", self)
        self.radionbutton2.setChecked(1 - int(browser.tabs_shape))
        self.radionbutton2.clicked.connect(self.tabs_design)
        self.radionbutton2.move(180, 200)

        self.tabs_color = QPushButton("Цвет вкладок", self)
        self.tabs_color.move(280, 205)
        self.tabs_color.adjustSize()
        self.tabs_color.clicked.connect(self.select_color)

        self.section3 = QLabel("Другое:", self)
        self.section3.move(5, 295)

        self.history_button = QPushButton("История запросов", self)
        self.history_button.move(100, 300)
        self.history_button.adjustSize()
        self.history_button.clicked.connect(self.open_history)

        self.promptings_delete_mode = QCheckBox("Режим удаления подсказок", self)
        self.promptings_delete_mode.adjustSize()
        self.promptings_delete_mode.clicked.connect(self.delete_mode)
        self.promptings_delete_mode.move(230, 305)

        # self.set_start_url = QComboBox(self)
        # self.set_start_url.addItems(["HomePage", "https://www.google.com"])

    def background_photo(self):  # выбрать фото на задний фон
        browser.home_page_image = QFileDialog.getOpenFileName(self, 'Выбрать картинку для фона', '')[0]
        browser.homepage_set_stylesheet()
        browser.cursor.execute(
            f"""UPDATE themes SET value = '{browser.home_page_image}' WHERE name = 'HomePageImage'""")
        browser.bd.commit()

    def delete_mode(self):  # режим удаления подсказок
        if self.promptings_delete_mode.isChecked():
            browser.delete_promptings = True
        else:
            for i in browser.findChildren(QPushButton)[1::]:
                browser.layout2.removeWidget(i)
                i.deleteLater()
                i = None
            browser.y_position = 1
            browser.x_position = 1
            browser.upload_promtings()
            browser.delete_promptings = False

    def tabs_design(self):  # дизайн вкладок
        if self.sender().text() == "Shaped":
            self.tabs_shape = True
        else:
            self.tabs_shape = False
        browser.tabs.setTabShape(self.tabs_shape)
        browser.cursor.execute(f"""UPDATE themes SET value = '{str(int(self.tabs_shape))}' WHERE name = 'TabsShape'""")
        browser.bd.commit()

    def select_color(self):  # выбор цвета
        self.color = QColorDialog.getColor()
        if self.sender().text() == "Цвет кнопок":
            self.button_color()
        elif self.sender().text() == "Цвет темы":
            self.browser_theme()
        elif self.sender().text() == "Цвет вкладок":
            self.set_tabs_color()

    def browser_theme(self):  # дизайн браузера
        if self.color.isValid():
            browser.setStyleSheet(f"""background-color: {self.color.name()}""")
            browser.cursor.execute(f"""UPDATE themes SET value = '{self.color.name()}' WHERE name = 'StartColor'""")
            browser.bd.commit()

    def button_color(self):  # дизайн кнопок, занесения нового дизайна в бд
        if self.color.isValid():
            browser.buttons_color = self.color.name()
            self.buttons_set_stylesheet()
            browser.cursor.execute(f"""UPDATE themes SET value = '{self.color.name()}' WHERE name = 'ButtonsColor'""")
            browser.bd.commit()

    def buttons_set_stylesheet(self):  # применить новый дизайн кнопок
        self.setStyleSheet(f"""QPushButton {{
                    background-color: {browser.buttons_color};
                    padding: 5px;
                    border-radius: 2px;
                    }}
                """)

    def set_tabs_color(self):  # установить цвет вкладок
        browser.color_of_tabs = self.color.name()
        browser.tabs_set_style_sheet()
        browser.cursor.execute(f"""UPDATE themes SET value = '{self.color.name()}' WHERE name = 'TabsColor'""")
        browser.bd.commit()

    def open_history(self):  # открыть историю браузера
        history.show()


class HistoryWindow(QMainWindow):  # окно истории запросов
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):  # создание окна, элементы окна
        self.check_list = []
        self.setGeometry(500, 500, 1000, 500)
        self.setWindowTitle("История запросов")
        self.setWindowIcon(QIcon("icons/history.png"))
        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)
        self.layout = QGridLayout(self.centralwidget)
        self.table = QTableWidget(0, 5, self)
        self.table.setFocusPolicy(Qt.NoFocus)

        # self.table.resize(500, 500)
        self.choose_all = QCheckBox("choose all", self)
        self.choose_all.stateChanged.connect(self.all_choose)

        self.toolbar = QToolBar(self)
        self.toolbar.setIconSize(QSize(20, 20))
        self.rubbish = QAction(QIcon("icons/rubbish.png"), "Delete", self)
        self.rubbish.triggered.connect(self.delete)
        self.restart = QAction(QIcon("icons/restart_page.png"), "Restart", self)
        self.restart.triggered.connect(self.restart_table)
        self.toolbar.addAction(self.rubbish)
        self.toolbar.addAction(self.restart)
        self.toolbar.addWidget(self.choose_all)
        self.toolbar.setStyleSheet("""spacing: 10px;""")
        self.addToolBar(self.toolbar)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.table)

        self.output_in_table()

    def output_in_table(self):  # внести данные в табличку
        count = browser.cursor.execute("""SELECT COUNT(*) FROM history""").fetchone()[0]
        result = browser.cursor.execute("""SELECT * FROM history""").fetchall()
        self.table.setRowCount(count)
        for i in range(len(result)):
            for j in range(1, 4):
                self.table.setItem(i, j - 1, QTableWidgetItem(str(result[i][j])))
            self.check = QCheckBox(self)
            self.button = QPushButton("Перейти", self)
            self.button.clicked.connect(self.open_url)
            self.widget = QWidget()
            self.cell_layout = QHBoxLayout(self.widget)
            self.cell_layout.setAlignment(Qt.AlignCenter)
            self.cell_layout.setContentsMargins(0, 0, 0, 0)
            self.cell_layout.addWidget(self.check)
            self.widget.setLayout(self.cell_layout)
            self.table.setCellWidget(i, 3, self.widget)
            self.table.setCellWidget(i, 4, self.button)
            self.check_list.append(self.check)
            self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            self.table.horizontalHeader().resizeSection(1, 150)
            self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

    def delete(self):  # удалить из таблицы
        for child in self.findChildren(QCheckBox)[1::]:
            if child.isChecked():
                # print(str(self.table.item(self.findChildren(QCheckBox)[1::].index(child), 2).text()))
                browser.cursor.execute(
                    f"""DELETE FROM history WHERE time =
                     '{str(self.table.item(self.findChildren(QCheckBox)[1::].index(child), 2).text())}'""")
                browser.bd.commit()
        self.output_in_table()
        self.choose_all.setChecked(False)

    def open_url(self):
        browser.new_tab(str(self.table.item(self.findChildren(QPushButton).index(self.sender()), 1).text()))

    def restart_table(self):  # перезагрузить таблицу
        self.output_in_table()

    def all_choose(self):  # выбрать все элементы таблицы
        if self.choose_all.isChecked():
            for child in self.findChildren(QCheckBox)[1::]:
                child.setChecked(True)
        else:
            for child in self.findChildren(QCheckBox)[1::]:
                child.setChecked(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = MainWindow()
    browser.show()
    settings = SettingsWindow()
    history = HistoryWindow()
    sys.exit(app.exec_())
