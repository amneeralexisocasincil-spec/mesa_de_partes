# -*- coding: utf-8 -*-
"""
registros.py
------------
Almacena los productos recibidos en ARREGLOS PARALELOS: la posición i de todos
los arreglos corresponde a un mismo registro (expediente).

    codigos[i], facturas[i], fechas_recepcion[i], ... describen el registro i.

Contiene las operaciones principales del sistema:
    - agregar_registro      (registrar con validación completa)
    - buscar_por_codigo     (búsqueda lineal)
    - ordenar               (ordenamiento por selección)
    - calcular_estado       (Vencido / Por vencer / Recibido)
    - actualizar_precio
"""
import calendar
from datetime import date

import validaciones as val

MESES_ALERTA = 3            # "Por vencer" = vence en 3 meses o menos
CODIGO_MAX = 9999           # ING-9999 es el último código posible

# --- Arreglos paralelos (un arreglo por campo) -----------------------------
codigos = []
facturas = []
fechas_recepcion = []
distribuidoras = []
rucs = []
productos = []
lotes = []
registros_sanitarios = []
cantidades = []
precios = []
vencimientos = []

# Lista con todos los arreglos: permite intercambiar, limpiar o medir todos a la vez.
ARREGLOS = [codigos, facturas, fechas_recepcion, distribuidoras, rucs, productos,
            lotes, registros_sanitarios, cantidades, precios, vencimientos]


def total():
    """Cantidad de registros almacenados."""
    return len(codigos)


def limpiar():
    """Vacía todos los arreglos (sin crear listas nuevas)."""
    for arreglo in ARREGLOS:
        arreglo.clear()


# ---------------------------------------------------------------------------
# Códigos
# ---------------------------------------------------------------------------
def generar_codigo():
    """Genera el siguiente código libre (ING-0001, ING-0002, ...).

    Toma el mayor número existente y le suma 1, así nunca se repite aunque los
    registros estén ordenados de otra forma. Devuelve None si ya se usó ING-9999.
    """
    mayor = 0
    for codigo in codigos:
        numero = int(codigo[4:])
        if numero > mayor:
            mayor = numero
    siguiente = mayor + 1
    if siguiente > CODIGO_MAX:
        return None
    return f"ING-{siguiente:04d}"


def buscar_por_codigo(codigo):
    """BÚSQUEDA LINEAL: recorre los códigos uno por uno.

    Devuelve la posición (índice) del registro o -1 si no existe.
    Acepta 'ing-0002', ' ING-0002 ' o solo '2'.
    """
    codigo = val.normalizar_codigo(codigo)
    for i in range(len(codigos)):
        if codigos[i] == codigo:
            return i
    return -1


# ---------------------------------------------------------------------------
# Registrar
# ---------------------------------------------------------------------------
def agregar_registro(codigo, factura, fecha_recepcion, distribuidora, ruc,
                     producto, lote, registro_sanitario, cantidad, precio,
                     vencimiento):
    """Valida TODOS los datos y, solo si todo es correcto, agrega el registro.

    Devuelve (True, mensaje) si se agregó, o (False, motivo) si se rechazó.
    Como los arreglos se modifican únicamente al final, nunca quedan
    desalineados aunque un dato sea inválido.
    """
    ok, codigo = val.validar_codigo(str(codigo).strip().upper())
    if not ok:
        return False, codigo
    if buscar_por_codigo(codigo) != -1:
        return False, f"El código {codigo} ya existe (no se permiten códigos repetidos)."

    ok, factura = val.validar_factura(factura)
    if not ok:
        return False, factura
    ok, fecha_recepcion = val.validar_fecha_recepcion(fecha_recepcion)
    if not ok:
        return False, fecha_recepcion
    ok, distribuidora = val.validar_texto(distribuidora, "Distribuidora")
    if not ok:
        return False, distribuidora
    ok, ruc = val.validar_ruc(ruc)
    if not ok:
        return False, ruc
    ok, producto = val.validar_texto(producto, "Producto")
    if not ok:
        return False, producto
    ok, lote = val.validar_lote(lote)
    if not ok:
        return False, lote
    ok, registro_sanitario = val.validar_registro_sanitario(registro_sanitario)
    if not ok:
        return False, registro_sanitario
    ok, cantidad = val.validar_cantidad(str(cantidad))
    if not ok:
        return False, cantidad
    ok, precio = val.validar_precio(str(precio))
    if not ok:
        return False, precio
    ok, vencimiento = val.validar_vencimiento(vencimiento, fecha_recepcion)
    if not ok:
        return False, vencimiento

    codigos.append(codigo)
    facturas.append(factura)
    fechas_recepcion.append(fecha_recepcion)
    distribuidoras.append(distribuidora)
    rucs.append(ruc)
    productos.append(producto)
    lotes.append(lote)
    registros_sanitarios.append(registro_sanitario)
    cantidades.append(cantidad)
    precios.append(precio)
    vencimientos.append(vencimiento)
    return True, f"Registro {codigo} guardado correctamente."


def actualizar_precio(codigo, precio):
    """Cambia el precio de un registro. Devuelve (True, precio_nuevo) o (False, motivo)."""
    indice = buscar_por_codigo(codigo)
    if indice == -1:
        return False, "No existe ningún registro con ese código."
    ok, valor = val.validar_precio(str(precio))
    if not ok:
        return False, valor
    precios[indice] = valor
    return True, valor


# ---------------------------------------------------------------------------
# Estado de vencimiento
# ---------------------------------------------------------------------------
def sumar_meses(fecha, meses):
    """Suma meses a una fecha ajustando el día si el mes destino es más corto
    (31/01 + 1 mes = 28/02)."""
    posicion = fecha.year * 12 + (fecha.month - 1) + meses
    anio = posicion // 12
    mes = posicion % 12 + 1
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def calcular_estado(vencimiento, hoy=None):
    """Devuelve 'Vencido', 'Por vencer' o 'Recibido' según la fecha de hoy.

    - Vencido:    el último día del mes de vencimiento ya pasó.
    - Por vencer: vence dentro de los próximos 3 meses (o hoy mismo).
    - Recibido:   vence más adelante.
    """
    if hoy is None:
        hoy = date.today()
    fin_de_mes = val.convertir_vencimiento(vencimiento)
    if fin_de_mes is None:
        return "Desconocido"
    if fin_de_mes < hoy:
        return "Vencido"
    if fin_de_mes <= sumar_meses(hoy, MESES_ALERTA):
        return "Por vencer"
    return "Recibido"


def dias_restantes(vencimiento, hoy=None):
    """Días que faltan hasta el último día del mes de vencimiento (negativo si ya venció)."""
    if hoy is None:
        hoy = date.today()
    fin_de_mes = val.convertir_vencimiento(vencimiento)
    return (fin_de_mes - hoy).days


def indices_por_estado(estado, hoy=None):
    """Lista de posiciones de los registros que tienen el estado indicado."""
    resultado = []
    for i in range(len(codigos)):
        if calcular_estado(vencimientos[i], hoy) == estado:
            resultado.append(i)
    return resultado


def contar_estados(hoy=None):
    """Devuelve (vencidos, por_vencer, recibidos)."""
    return (len(indices_por_estado("Vencido", hoy)),
            len(indices_por_estado("Por vencer", hoy)),
            len(indices_por_estado("Recibido", hoy)))


# ---------------------------------------------------------------------------
# Ordenamiento
# ---------------------------------------------------------------------------
def _clave(i, criterio):
    """Valor por el que se compara el registro i (con el código como desempate)."""
    if criterio == "vencimiento":
        mes, anio = vencimientos[i].split("/")
        return (int(anio) * 100 + int(mes), codigos[i])
    return (codigos[i],)


def ordenar(criterio):
    """ORDENAMIENTO POR SELECCIÓN (ascendente) sobre todos los arreglos paralelos.

    criterio: 'codigo' o 'vencimiento'.
    En cada vuelta busca el menor de los elementos restantes y lo intercambia
    con el de la posición i, moviendo TODOS los arreglos para que los datos de
    cada registro sigan juntos.
    """
    if criterio != "codigo" and criterio != "vencimiento":
        raise ValueError("criterio debe ser 'codigo' o 'vencimiento'")
    n = len(codigos)
    for i in range(n - 1):
        posicion_menor = i
        for j in range(i + 1, n):
            if _clave(j, criterio) < _clave(posicion_menor, criterio):
                posicion_menor = j
        if posicion_menor != i:
            for arreglo in ARREGLOS:
                arreglo[i], arreglo[posicion_menor] = arreglo[posicion_menor], arreglo[i]
