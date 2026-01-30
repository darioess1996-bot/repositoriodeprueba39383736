import sys
import math
import random
from PySide6.QtCore import QTimer, Qt, QPointF
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QLinearGradient, QBrush, QPainterPath, QKeyEvent

class IntroViaLactea(QWidget):
    def __init__(self, al_terminar):
        super().__init__()
        self.al_terminar = al_terminar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.showFullScreen()
        
        self.zoom = 0.06
        self.fase = "ZOOM"
        self.radio_atomo = 0 
        self.nivel_leche = 0.0
        self.opacidad_slogan = 0
        self.angulo_atomo = 0.0
        self.ya_disparado = False 

        self.estrellas = [[random.uniform(-1, 1), random.uniform(-1, 1), random.random()] for _ in range(400)]
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.engine)
        self.timer.start(16)

    # SALIDA DE EMERGENCIA EN LA INTRO
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            sys.exit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        painter.fillRect(self.rect(), QColor("#02040a"))
        
        if self.fase in ["ZOOM", "ORBITA"]:
            for e in self.estrellas:
                ex = cx + (e[0] * self.zoom * 1500)
                ey = cy + (e[1] * self.zoom * 1500)
                size = e[2] * 1.5 * (self.zoom * 5)
                if 0 < ex < self.width() and 0 < ey < self.height():
                    opacidad = min(255, int(self.zoom * 300 * e[2]))
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(255, 255, 255, opacidad))
                    painter.drawEllipse(QPointF(ex, ey), size, size)

        if self.fase in ["ZOOM", "ORBITA"]:
            opacidad_ps = min(255, int((self.zoom - 0.2) * 400)) if self.zoom > 0.2 else 0
            if opacidad_ps > 0:
                painter.setPen(QPen(QColor(56, 139, 253, opacidad_ps), 2))
                painter.setBrush(QColor(13, 17, 27, opacidad_ps))
                painter.drawEllipse(QPointF(cx, cy), 60, 60)
                painter.setPen(QColor(56, 139, 253, opacidad_ps))
                painter.setFont(QFont("Arial", 25, QFont.Bold))
                painter.drawText(self.rect(), Qt.AlignCenter, "PS")

            if self.fase == "ORBITA":
                iconos = ["🥛", "🌾", "🐮", "📊"]
                for i in range(4):
                    ang = math.radians(self.angulo_atomo + (i * 90))
                    ex = cx + (self.radio_atomo * math.cos(ang))
                    ey = cy + (self.radio_atomo * 0.5 * math.sin(ang))
                    painter.setFont(QFont("Arial", 25))
                    painter.drawText(int(ex-15), int(ey+10), iconos[i])

        if self.fase in ["LLENADO", "SLOGAN"]:
            self.dibujar_leche(painter)
            if self.fase == "SLOGAN":
                painter.setPen(QColor(30, 60, 110, self.opacidad_slogan))
                painter.setFont(QFont("Verdana", 50, QFont.Bold))
                painter.drawText(self.rect(), Qt.AlignCenter, "VÍA LÁCTEA")

    def engine(self):
        self.angulo_atomo += 4
        if self.fase == "ZOOM":
            self.zoom *= 1.04
            if self.zoom >= 1.2: self.fase = "ORBITA"
        elif self.fase == "ORBITA":
            if self.radio_atomo < 250: self.radio_atomo += 5
            else: QTimer.singleShot(2500, self.activar_leche)
        elif self.fase == "LLENADO":
            if self.nivel_leche < self.height() + 100:
                self.nivel_leche += (self.nivel_leche * 0.02) + 5
            else: self.fase = "SLOGAN"
        elif self.fase == "SLOGAN":
            if self.opacidad_slogan < 255: self.opacidad_slogan += 5
            else:
                if not self.ya_disparado:
                    self.ya_disparado = True
                    QTimer.singleShot(200, self.terminar_intro)
        self.update()

    def dibujar_leche(self, painter):
        y_base = self.height() - self.nivel_leche
        path = QPainterPath()
        path.moveTo(0, self.height())
        path.lineTo(0, y_base)
        for x in range(0, self.width() + 25, 25):
            onda = 15 * math.sin(x * 0.005 + (self.angulo_atomo * 0.1))
            path.lineTo(x, y_base + onda)
        path.lineTo(self.width(), self.height())
        grad = QLinearGradient(0, y_base, 0, self.height())
        grad.setColorAt(0, QColor("#FFFFFF"))
        grad.setColorAt(1, QColor("#F2F2F2"))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

    def activar_leche(self):
        if self.fase == "ORBITA": self.fase = "LLENADO"

    def terminar_intro(self):
        self.timer.stop()
        self.al_terminar()
        self.hide()
        self.deleteLater()
