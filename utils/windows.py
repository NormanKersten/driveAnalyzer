from ctypes import windll


# High-DPI für Windows 10, z.B. für Texte usw.
def set_dpi_awareness():
    try:
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
