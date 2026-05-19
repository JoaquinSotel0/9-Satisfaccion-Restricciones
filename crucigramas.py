import csps
import time


class Crucigrama(csps.ProblemaCSP):
    def __init__(self, pos_ini):
        self.X = # TODO: definir el conjunto de variables
        self.D = # TODO: definir el dominio de cada variable
        self.N = # TODO: definir el conjunto de vecinos de cada variable
        

    def restriccion_binaria(self, xi, vi, xj, vj):
        # TODO: definir la función de restricción binaria entre las variables xi y xj
        pass
    
def prueba_crucigrama(verticales, horizontales, consistencia=1):
    
    # TODO: Probar el CSP del crucigrama con el grafo de restricciones con consistencia dada y medir el tiempo que tarda en resolverlo. Imprimir la asignación resultante, el número de backtrackings realizados y el tiempo que tardó en resolverlo.
    
    raise NotImplementedError("Completa la función prueba_crucigrama para probar tu implementación del CSP del crucigrama")

if __name__ == "__main__":
    
    prueba_crucigrama(...) # TODO: definir los crucigramas a probar

         
