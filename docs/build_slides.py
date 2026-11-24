"""Build the editable repository copy of the five-slide MMA presentation.

Install the optional authoring dependency with: pip install python-pptx
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt


DESTINATION = Path(__file__).with_name("mma-estilos-y-prediccion.pptx")
BACKGROUND = RGBColor(16, 23, 29)
ACCENT = RGBColor(105, 215, 196)
TEXT = RGBColor(237, 242, 244)

SLIDES = [
    ("MMA: estilos y predicción de combates", ["Tres preguntas sobre 6,743 peleas UFC de 2013 a 2026"]),
    ("Pregunta 1 · ¿Qué estilos se enfrentan?", [
        "Clasificamos cada trayectoria previa como golpeador, luchador, sometedor o mixto.",
        "La etiqueta describe conducta en peleas UFC, no una disciplina declarada.",
        "Con menos de tres peleas, el estilo queda sin historial.",
    ]),
    ("Pregunta 2 · ¿Qué cruces terminan antes?", [
        "Golpeador × Luchador: 494 peleas, 49.6% de finalizaciones.",
        "Luchador × Sometedor: 360 peleas, 56.9% de finalizaciones.",
        "Son asociaciones históricas, no efectos causales.",
    ]),
    ("Pregunta 3 · ¿Qué tan predecible es ganar?", [
        "Prueba cronológica: 948 combates en 2025–2026.",
        "Modelo de historiales: 63.2% de acierto.",
        "En las 937 peleas con cuotas, el modelo acertó 63.5% y las cuotas iniciales 66.6%.",
        "La incertidumbre sigue siendo considerable.",
    ]),
    ("Conclusión · Lo que sí podemos afirmar", [
        "Los cruces de estilos muestran diferencias en finalización y victoria.",
        "Las cuotas iniciales superaron al modelo de historiales en la prueba.",
        "Para afinar el análisis: controlar división, época y nivel del rival.",
        "Fuente: UFC Data v0.1.1, Bair (2026), CC BY 4.0.",
    ]),
]


def add_text(slide, content, left, top, width, height, size, color, bold=False):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Inches(0.02)
    frame.margin_top = frame.margin_bottom = Inches(0.01)
    for index, line in enumerate(content):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.space_after = Pt(14)
        for run in paragraph.runs:
            run.font.name = "Aptos"
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = color


def main():
    deck = Presentation()
    deck.slide_width = Inches(13.333)
    deck.slide_height = Inches(7.5)
    for index, (title, lines) in enumerate(SLIDES):
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = BACKGROUND
        add_text(slide, [title], .86, .72 if index else 1.82, 11.6, 1.2, 34 if index else 41, ACCENT, True)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.85), Inches(1.85 if index else 3.05), Inches(.98), Inches(.07))
        bar.fill.solid()
        bar.fill.fore_color.rgb = ACCENT
        bar.line.fill.background()
        add_text(slide, lines, 1.01, 2.28 if index else 3.35, 11.1, 4.3 if index else 1.4, 22 if index else 24, TEXT)
    deck.save(DESTINATION)
    print(f"{DESTINATION} · {len(deck.slides)} diapositivas")


if __name__ == "__main__":
    main()
