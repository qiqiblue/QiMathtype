import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    """应用程序入口函数。"""
    app = QApplication(sys.argv)
    app.setApplicationName("QiMathType MVP")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
