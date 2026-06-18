#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
crucigramas.py
---------------

Modelo CSP para construir crucigramas a partir de palabras horizontales
y verticales.
"""

import csps
import time


class Crucigrama(csps.ProblemaCSP):

    def __init__(self, verticales, horizontales, filas=10, columnas=10):
        """
        Inicializa el problema CSP del crucigrama.

        @param verticales: lista de palabras que deben colocarse verticalmente.
        @param horizontales: lista de palabras que deben colocarse horizontalmente.
        @param filas: número de filas de la retícula.
        @param columnas: número de columnas de la retícula.
        """
        self.verticales = [p.upper() for p in verticales]
        self.horizontales = [p.upper() for p in horizontales]
        self.filas = filas
        self.columnas = columnas

        # Cada palabra es una variable.
        # H0, H1, ... son horizontales.
        # V0, V1, ... son verticales.
        self.palabras = {}

        for i, palabra in enumerate(self.horizontales):
            self.palabras[f"H{i}"] = palabra

        for i, palabra in enumerate(self.verticales):
            self.palabras[f"V{i}"] = palabra

        self.X = set(self.palabras.keys())

        # Dominio: posiciones posibles donde cabe cada palabra.
        self.D = {}

        for var in self.X:
            palabra = self.palabras[var]

            if var.startswith("H"):
                self.D[var] = self.dominio_horizontal(palabra)
            else:
                self.D[var] = self.dominio_vertical(palabra)

        # Todos son vecinos de todos, porque cualquier par de palabras
        # puede tener conflicto en la retícula.
        self.N = {
            var: self.X - {var}
            for var in self.X
        }

    def dominio_horizontal(self, palabra):
        """
        Genera todas las posiciones válidas para una palabra horizontal.

        Un valor del dominio tiene la forma:
        (fila, columna, "H")
        """
        dominio = set()

        for fila in range(self.filas):
            for columna in range(self.columnas - len(palabra) + 1):
                dominio.add((fila, columna, "H"))

        return dominio

    def dominio_vertical(self, palabra):
        """
        Genera todas las posiciones válidas para una palabra vertical.

        Un valor del dominio tiene la forma:
        (fila, columna, "V")
        """
        dominio = set()

        for fila in range(self.filas - len(palabra) + 1):
            for columna in range(self.columnas):
                dominio.add((fila, columna, "V"))

        return dominio

    def celdas_ocupadas(self, variable, valor):
        """
        Devuelve un diccionario con las celdas ocupadas por una palabra.

        Las llaves son posiciones (fila, columna) y los valores son letras.
        """
        palabra = self.palabras[variable]
        fila, columna, direccion = valor

        celdas = {}

        for i, letra in enumerate(palabra):
            if direccion == "H":
                celdas[(fila, columna + i)] = letra
            else:
                celdas[(fila + i, columna)] = letra

        return celdas

    def restriccion_binaria(self, xi, vi, xj, vj):
        """
        Verifica si dos palabras pueden colocarse simultáneamente.

        Reglas:
        1. Si ocupan una misma celda, la letra debe ser la misma.
        2. Dos palabras en la misma dirección no pueden tocarse ni encimarse.
        3. Palabras perpendiculares pueden cruzarse solo si coinciden en letra.
        """
        celdas_i = self.celdas_ocupadas(xi, vi)
        celdas_j = self.celdas_ocupadas(xj, vj)

        direccion_i = vi[2]
        direccion_j = vj[2]

        # Caso 1: revisar intersecciones.
        interseccion = set(celdas_i.keys()) & set(celdas_j.keys())

        for celda in interseccion:
            if celdas_i[celda] != celdas_j[celda]:
                return False

        # Si son palabras en la misma dirección, no deben translaparse.
        if direccion_i == direccion_j:
            if interseccion:
                return False

            # Tampoco deben ir pegadas.
            for fila_i, col_i in celdas_i:
                for fila_j, col_j in celdas_j:

                    # Horizontales: no deben estar en filas vecinas
                    # compartiendo columnas cercanas.
                    if direccion_i == "H":
                        if abs(fila_i - fila_j) <= 1 and col_i == col_j:
                            return False

                    # Verticales: no deben estar en columnas vecinas
                    # compartiendo filas cercanas.
                    if direccion_i == "V":
                        if abs(col_i - col_j) <= 1 and fila_i == fila_j:
                            return False

        # Si son perpendiculares, pueden cruzarse con letra igual.
        # Si no se cruzan, también es permitido por ahora.
        return True

    def cruces_por_variable(self, asignacion):
        """
        Cuenta cuántos cruces válidos tiene cada palabra en una asignación.
        """
        cruces = {var: 0 for var in asignacion}

        variables = list(asignacion.keys())

        for i in range(len(variables)):
            for j in range(i + 1, len(variables)):
                xi = variables[i]
                xj = variables[j]
                vi = asignacion[xi]
                vj = asignacion[xj]

                if vi[2] == vj[2]:
                    continue

                celdas_i = self.celdas_ocupadas(xi, vi)
                celdas_j = self.celdas_ocupadas(xj, vj)

                interseccion = set(celdas_i.keys()) & set(celdas_j.keys())

                if interseccion:
                    cruces[xi] += 1
                    cruces[xj] += 1

        return cruces

    def asignacion_valida_globalmente(self, asignacion):
        """
        Verifica la restricción global:
        cada palabra debe cruzar con al menos una palabra perpendicular.
        """
        cruces = self.cruces_por_variable(asignacion)
        return all(cruces[var] >= 1 for var in cruces)

    def hay_cruce(self, xi, vi, xj, vj):
        """
        Regresa True si dos palabras perpendiculares se cruzan en una celda.
        Se asume que la restricción binaria ya valida que la letra coincida.
        """
        if vi[2] == vj[2]:
            return False

        celdas_i = self.celdas_ocupadas(xi, vi)
        celdas_j = self.celdas_ocupadas(xj, vj)

        return bool(set(celdas_i.keys()) & set(celdas_j.keys()))

    def puede_cruzar_con_alguien(self, variable, valor, asignacion):
        """
        Verifica si una palabra ya cruza o todavía puede cruzar con alguna
        palabra perpendicular no asignada.
        """
        for otra, valor_otra in asignacion.items():
            if self.hay_cruce(variable, valor, otra, valor_otra):
                return True

        for otra in self.X:
            if otra == variable or otra in asignacion:
                continue
            if self.palabras[otra] == self.palabras[variable]:
                continue
            if otra[0] == variable[0]:
                continue
            for valor_otra in self.D[otra]:
                if self.restriccion_binaria(variable, valor, otra, valor_otra):
                    if self.hay_cruce(variable, valor, otra, valor_otra):
                        return True

        return False

    def imprimir_crucigrama(self, asignacion):
        """
        Imprime la retícula del crucigrama.
        """
        tablero = [["." for _ in range(self.columnas)]
                   for _ in range(self.filas)]

        for var, valor in asignacion.items():
            palabra = self.palabras[var]
            fila, columna, direccion = valor

            for i, letra in enumerate(palabra):
                if direccion == "H":
                    tablero[fila][columna + i] = letra
                else:
                    tablero[fila + i][columna] = letra

        for fila in tablero:
            print(" ".join(fila))
def asignacion_crucigrama(csp, asignacion=None):
    """
    Búsqueda por backtracking específica para el crucigrama.

    Esta versión ordena los valores que producen cruces primero y poda
    asignaciones parciales donde alguna palabra ya no puede cruzar con otra.
    """
    if asignacion is None:
        asignacion = {}

    if set(asignacion.keys()) == csp.X:
        if csp.asignacion_valida_globalmente(asignacion):
            return asignacion.copy()
        csp.backtracking += 1
        return None

    # Selecciona la variable no asignada con dominio más pequeño.
    var = min(
        [x for x in csp.X if x not in asignacion],
        key=lambda x: len(csp.D[x])
    )

    def puntuacion_valor(valor):
        """
        Favorece valores que cruzan con palabras ya asignadas o que tienen
        muchas posibilidades de cruzar con palabras pendientes.
        """
        puntos = 0

        for otra, valor_otra in asignacion.items():
            if csp.restriccion_binaria(var, valor, otra, valor_otra):
                if csp.hay_cruce(var, valor, otra, valor_otra):
                    puntos += 100
            else:
                return -1

        for otra in csp.X:
            if otra == var or otra in asignacion or otra[0] == var[0]:
                continue
            for valor_otra in csp.D[otra]:
                if csp.restriccion_binaria(var, valor, otra, valor_otra):
                    if csp.hay_cruce(var, valor, otra, valor_otra):
                        puntos += 1

        return puntos

    valores = sorted(csp.D[var], key=puntuacion_valor, reverse=True)

    for val in valores:
        if puntuacion_valor(val) < 0:
            continue

        es_valido = True

        for var_asignada, val_asignado in asignacion.items():
            if var_asignada in csp.N[var]:
                if not csp.restriccion_binaria(var, val,
                                               var_asignada, val_asignado):
                    es_valido = False
                    break

        if not es_valido:
            continue

        if not csp.puede_cruzar_con_alguien(var, val, asignacion):
            continue

        asignacion[var] = val

        # Poda: toda palabra asignada debe cruzar ya o poder cruzar todavía
        # con alguna palabra pendiente.
        posible = True
        for variable, valor in asignacion.items():
            asignacion_sin_variable = {
                x: v for x, v in asignacion.items() if x != variable
            }
            if not csp.puede_cruzar_con_alguien(
                variable,
                valor,
                asignacion_sin_variable
            ):
                posible = False
                break

        if posible:
            resultado = asignacion_crucigrama(csp, asignacion)
            if resultado is not None:
                return resultado

        del asignacion[var]

    csp.backtracking += 1
    return None

def leer_palabras(nombre_archivo):
    """
    Lee palabras de un archivo de texto, una palabra por línea.
    """
    palabras = []

    with open(nombre_archivo, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            palabra = linea.strip()
            if palabra:
                palabras.append(palabra)

    return palabras


def prueba_crucigrama(verticales, horizontales, filas=10, columnas=10,
                      consistencia=1):
    """
    Prueba el CSP del crucigrama y mide el tiempo de solución.
    """
    problema = Crucigrama(verticales, horizontales, filas, columnas)

    inicio = time.time()
    problema.backtracking = 0
    asignacion = asignacion_crucigrama(problema)
    fin = time.time()

    print("\n" + "=" * 50)
    print("Prueba de crucigrama")
    print("=" * 50)
    print("Filas:", filas)
    print("Columnas:", columnas)
    print("Consistencia:", consistencia)
    print("Tiempo:", fin - inicio)
    print("Backtrackings:", problema.backtracking)

    if asignacion is None:
        print("No se encontró solución. Se necesita una retícula más grande.")
        return None

    if not problema.asignacion_valida_globalmente(asignacion):
        print("Se encontró una asignación, pero no todas las palabras cruzan.")
        print("Conviene probar con una retícula distinta o más palabras.")
        problema.imprimir_crucigrama(asignacion)
        return asignacion

    print("\nAsignación encontrada:")
    for var, val in asignacion.items():
        print(var, problema.palabras[var], "->", val)

    print("\nCrucigrama:")
    problema.imprimir_crucigrama(asignacion)

    return asignacion

if __name__ == "__main__":

    verticales = leer_palabras("verticales.txt")
    horizontales = leer_palabras("horizontales.txt")

    prueba_crucigrama(
        verticales,
        horizontales,
        filas=12,
        columnas=12,
        consistencia=1
    )