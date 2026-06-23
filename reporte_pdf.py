import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage
)


# ── Paleta de colores ──────────────────────────────────────────────────────────
AZUL         = colors.HexColor("#1565C0")
AZUL_CLARO   = colors.HexColor("#E3F2FD")
ROJO         = colors.HexColor("#B71C1C")
ROJO_CLARO   = colors.HexColor("#FFEBEE")
VERDE        = colors.HexColor("#2E7D32")
VERDE_CLARO  = colors.HexColor("#E8F5E9")
AMARILLO     = colors.HexColor("#F9A825")
AMARILLO_CLARO = colors.HexColor("#FFFDE7")
GRIS_CLARO   = colors.HexColor("#F5F5F5")
GRIS_TEXTO   = colors.HexColor("#424242")


def _estilos():
    base = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=base["Title"],
        fontSize=20,
        textColor=AZUL,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=base["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#757575"),
        spaceAfter=2,
        alignment=TA_CENTER,
    )
    seccion = ParagraphStyle(
        "Seccion",
        parent=base["Heading2"],
        fontSize=12,
        textColor=AZUL,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
        borderPad=4,
    )
    normal = ParagraphStyle(
        "NormalCustom",
        parent=base["Normal"],
        fontSize=10,
        textColor=GRIS_TEXTO,
        spaceAfter=4,
        leading=14,
    )
    rec_item = ParagraphStyle(
        "RecItem",
        parent=base["Normal"],
        fontSize=9,
        textColor=GRIS_TEXTO,
        spaceAfter=5,
        leading=13,
        leftIndent=8,
    )
    footer = ParagraphStyle(
        "Footer",
        parent=base["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#9E9E9E"),
        alignment=TA_CENTER,
    )
    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "seccion": seccion,
        "normal": normal,
        "rec_item": rec_item,
        "footer": footer,
    }


def _grafico_zscores(z_talla, z_peso, z_peso_talla, z_imc) -> io.BytesIO:
    """Genera gráfico de barras horizontales con los z-scores."""
    labels   = ["Talla/Edad", "Peso/Edad", "Peso/Talla", "IMC"]
    valores  = [z_talla, z_peso, z_peso_talla, z_imc]

    def color_z(v):
        if v < -2:   return "#EF5350"
        elif v < 0:  return "#FFA726"
        elif v <= 2: return "#66BB6A"
        else:        return "#42A5F5"

    colores_barras = [color_z(v) for v in valores]

    fig, ax = plt.subplots(figsize=(5.5, 2.4))
    y_pos = np.arange(len(labels))
    bars  = ax.barh(y_pos, valores, color=colores_barras, height=0.5, edgecolor="white")

    # Líneas de referencia
    ax.axvline(0,  color="#616161", linewidth=1.0, linestyle="-")
    ax.axvline(-2, color="#EF5350", linewidth=0.8, linestyle="--", alpha=0.7)
    ax.axvline(2,  color="#42A5F5", linewidth=0.8, linestyle="--", alpha=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Z-score", fontsize=9)
    ax.set_xlim(-4, 4)
    ax.set_title("Z-scores antropométricos (OMS)", fontsize=10, fontweight="bold", pad=8)
    ax.tick_params(axis="x", labelsize=8)

    # Etiquetas de valores
    for bar, val in zip(bars, valores):
        ax.text(
            val + (0.1 if val >= 0 else -0.1),
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}",
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=8, color="#212121"
        )

    # Leyenda
    parches = [
        mpatches.Patch(color="#EF5350", label="< -2 (Déficit)"),
        mpatches.Patch(color="#FFA726", label="-2 a 0"),
        mpatches.Patch(color="#66BB6A", label="0 a 2 (Normal)"),
        mpatches.Patch(color="#42A5F5", label="> 2 (Exceso)"),
    ]
    ax.legend(handles=parches, fontsize=7, loc="lower right",
              framealpha=0.8, ncol=2)

    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _grafico_probabilidad(proba: float) -> io.BytesIO:
    """Genera gauge semicircular de probabilidad de anemia."""
    fig, ax = plt.subplots(figsize=(3.5, 2.0), subplot_kw={"aspect": "equal"})

    theta = np.linspace(np.pi, 0, 300)

    # Fondo del gauge (arco gris)
    ax.plot(np.cos(theta), np.sin(theta), color="#E0E0E0", linewidth=18, solid_capstyle="round")

    # Color según probabilidad
    if proba < 0.35:
        color_gauge = "#4CAF50"
    elif proba < 0.60:
        color_gauge = "#FFC107"
    else:
        color_gauge = "#F44336"

    # Arco de probabilidad
    theta_fill = np.linspace(np.pi, np.pi - np.pi * proba, 300)
    ax.plot(np.cos(theta_fill), np.sin(theta_fill),
            color=color_gauge, linewidth=18, solid_capstyle="round")

    # Texto central
    ax.text(0, 0.0, f"{proba:.1%}", ha="center", va="center",
            fontsize=16, fontweight="bold", color=color_gauge)
    ax.text(0, -0.35, "Probabilidad\nde anemia", ha="center", va="center",
            fontsize=8, color="#616161")

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.5, 1.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.2)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def generar_reporte_pdf(
    edad_meses: int,
    peso_kg: float,
    talla_cm: float,
    altitud: int,
    sexo: str,
    area: str,
    departamento: str,
    z_talla: float,
    z_peso: float,
    z_peso_talla: float,
    z_imc: float,
    resultado: str,
    proba: float,
    urgencia: str,
    recomendaciones: list,
) -> bytes:
    """
    Genera el PDF completo y retorna los bytes para descarga en Streamlit.
    """
    buf_pdf  = io.BytesIO()
    estilos  = _estilos()
    doc      = SimpleDocTemplate(
        buf_pdf,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
    )
    W = A4[0] - 4*cm   # ancho disponible
    historia = []

    # ── ENCABEZADO ──────────────────────────────────────────────────────────
    historia.append(Paragraph("🩺 Reporte de Evaluación de Anemia Infantil", estilos["titulo"]))
    historia.append(Paragraph("Sistema de Detección Basado en Machine Learning — ENDES 2019–2024", estilos["subtitulo"]))
    historia.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} · Grupo 01 — USIL · Agentes Inteligentes 2026-1",
        estilos["subtitulo"]
    ))
    historia.append(HRFlowable(width=W, thickness=2, color=AZUL, spaceAfter=10))

    # ── DATOS DEL NIÑO ───────────────────────────────────────────────────────
    historia.append(Paragraph("Datos del Niño Evaluado", estilos["seccion"]))

    sexo_label = "Masculino" if sexo == "M" else "Femenino"
    anios      = edad_meses // 12
    meses_r    = edad_meses % 12
    edad_str   = f"{anios} año(s) y {meses_r} mes(es) ({edad_meses} meses)"

    datos_nino = [
        ["Campo",              "Valor",       "Campo",           "Valor"],
        ["Edad",               edad_str,      "Sexo",            sexo_label],
        ["Peso",               f"{peso_kg} kg","Talla",          f"{talla_cm} cm"],
        ["Área de residencia", area,           "Departamento",    departamento],
        ["Altitud",            f"{altitud} msnm", "", ""],
    ]

    tabla_datos = Table(datos_nino, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    tabla_datos.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("BACKGROUND",   (0, 1), (-1, -1), GRIS_CLARO),
        ("BACKGROUND",   (0, 2), (-1, 2), colors.white),
        ("BACKGROUND",   (0, 4), (-1, 4), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#BDBDBD")),
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("FONTNAME",     (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",     (2, 1), (2, -1), "Helvetica-Bold"),
    ]))
    historia.append(tabla_datos)

    # ── RESULTADO ────────────────────────────────────────────────────────────
    historia.append(Paragraph("Resultado de la Predicción", estilos["seccion"]))

    # Gauge de probabilidad + cuadro resultado en paralelo
    buf_gauge = _grafico_probabilidad(proba)
    img_gauge = RLImage(buf_gauge, width=5.5*cm, height=3.2*cm)

    color_fondo = ROJO_CLARO if resultado == "Con anemia" else VERDE_CLARO
    color_texto = ROJO       if resultado == "Con anemia" else VERDE
    icono       = "⚠️" if resultado == "Con anemia" else "✅"

    urgencia_texto = {
        "alta":     "🔴 Requiere atención URGENTE",
        "moderada": "🟡 Se recomienda consulta médica",
        "normal":   "🟢 Sin urgencia inmediata",
    }.get(urgencia, "")

    resultado_contenido = [
        [Paragraph(f"<b>{icono} {resultado}</b>", ParagraphStyle(
            "Res", fontName="Helvetica-Bold", fontSize=14,
            textColor=color_texto, alignment=TA_CENTER))],
        [Paragraph(f"Probabilidad: <b>{proba:.1%}</b>", ParagraphStyle(
            "Prob", fontName="Helvetica", fontSize=11,
            textColor=GRIS_TEXTO, alignment=TA_CENTER))],
        [Paragraph(urgencia_texto, ParagraphStyle(
            "Urg", fontName="Helvetica", fontSize=9,
            textColor=GRIS_TEXTO, alignment=TA_CENTER))],
    ]
    tabla_res_interna = Table(resultado_contenido, colWidths=[8*cm])
    tabla_res_interna.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), color_fondo),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [5]),
    ]))

    tabla_resultado = Table([[img_gauge, tabla_res_interna]], colWidths=[6*cm, W - 6*cm])
    tabla_resultado.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",  (0, 0), (0, 0),   "CENTER"),
    ]))
    historia.append(tabla_resultado)

    # ── Z-SCORES ─────────────────────────────────────────────────────────────
    historia.append(Paragraph("Z-Scores Antropométricos (Tablas OMS)", estilos["seccion"]))

    buf_zscores = _grafico_zscores(z_talla, z_peso, z_peso_talla, z_imc)
    img_zscores = RLImage(buf_zscores, width=W, height=W * 0.40)
    historia.append(img_zscores)

    historia.append(Spacer(1, 4))

    # Tabla numérica de z-scores
    tabla_z = Table([
        ["Indicador", "Z-score", "Interpretación"],
        ["Talla / Edad (T/E)",   f"{z_talla:.2f}",      _interpreta_z(z_talla)],
        ["Peso / Edad (P/E)",    f"{z_peso:.2f}",       _interpreta_z(z_peso)],
        ["Peso / Talla (P/T)",   f"{z_peso_talla:.2f}", _interpreta_z(z_peso_talla)],
        ["IMC",                  f"{z_imc:.2f}",        _interpreta_z(z_imc)],
    ], colWidths=[6*cm, 3*cm, W - 9*cm])

    tabla_z.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#BDBDBD")),
        ("ALIGN",        (1, 0), (1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    historia.append(tabla_z)

    # ── RECOMENDACIONES ──────────────────────────────────────────────────────
    historia.append(Paragraph("Recomendaciones", estilos["seccion"]))

    color_rec_fondo = ROJO_CLARO if urgencia == "alta" else (
        AMARILLO_CLARO if urgencia == "moderada" else VERDE_CLARO
    )

    for rec in recomendaciones:
        rec_limpia = rec.replace("•", "").replace("⚠️", "").replace("✅", "").strip()
        if not rec_limpia:
            continue
        p = Paragraph(f"• {rec_limpia}", estilos["rec_item"])
        tabla_rec = Table([[p]], colWidths=[W])
        tabla_rec.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), color_rec_fondo),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#E0E0E0")),
        ]))
        historia.append(tabla_rec)
        historia.append(Spacer(1, 2))

    # ── AVISO LEGAL ──────────────────────────────────────────────────────────
    historia.append(Spacer(1, 10))
    historia.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#BDBDBD"), spaceAfter=6))
    historia.append(Paragraph(
        "Este reporte es generado por un sistema de apoyo a la decisión basado en Machine Learning "
        "y NO reemplaza el diagnóstico clínico de un profesional de la salud. "
        "Los resultados deben ser interpretados por personal médico calificado.",
        ParagraphStyle("Aviso", fontSize=8, textColor=colors.HexColor("#757575"),
                       alignment=TA_CENTER, leading=11)
    ))
    historia.append(Spacer(1, 4))
    historia.append(Paragraph(
        "Grupo 01 — USIL | Agentes Inteligentes 2026-1 | Datos: ENDES 2019–2024 (INEI)",
        estilos["footer"]
    ))

    doc.build(historia)
    return buf_pdf.getvalue()


def _interpreta_z(z: float) -> str:
    if z < -3:   return "Desnutricion severa"
    elif z < -2: return "Desnutricion moderada"
    elif z < -1: return "Riesgo de desnutricion"
    elif z <= 1: return "Normal"
    elif z <= 2: return "Sobrepeso leve"
    else:        return "Obesidad / exceso"
