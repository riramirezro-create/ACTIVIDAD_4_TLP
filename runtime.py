# -*- coding: utf-8 -*-
# runtime.py (VERSION CON INTERFAZ GRAFICA USANDO Tkinter y caracteres ASCII unicamente)

import sys
import json
import time
import random
# Tkinter es la libreria GUI estandar de Python, compatible con 2.7
import Tkinter as tk
import tkMessageBox 

class Juego:
    def __init__(self, datos_juego):
        self.datos_juego = datos_juego
        self.tipo_juego = self.datos_juego.get('tipo_juego', 'TETRIS')
        
        # Leemos el nivel y las geometrias desde el JSON
        self.nivel = self.datos_juego.get('nivel', 'SNAKE')
        
        self.juego_iniciado = False
        self.shapes_geom = self.datos_juego.get('shapes_geom', {})
        
        config = self.datos_juego.get('config', {})
        self.ancho = config.get('grid_size', [10, 20])[0]
        self.alto = config.get('grid_size', [10, 20])[1]
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.puntuacion = 0
        self.juego_terminado = False
        
        # --- Configuracion de la GUI ---
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego + " (Nivel: " + self.nivel + ")")
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        self.taman_celda = 25 
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda
        
        self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=40, padx=10)
        
        self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover", bg='#222222', fg='gray', font=('Consolas', 10))
        self.label_controles.pack(pady=20, padx=10)

        self.root.bind('<Key>', self.manejar_input_gui)
        
        if self.tipo_juego == 'TETRIS':
            self.pieza_actual = None
            self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
            self.velocidad_gravedad = 0.4
        
        if self.tipo_juego == 'SNAKE':
            self.serpiente_cuerpo = []
            self.serpiente_direccion = (1, 0)
            
            # Variables para los items y obstaculos
            self.posicion_comida = None
            self.posicion_veneno = None
            self.posicion_estrella = None
            self.posiciones_obstaculos = []
            
            self.crecer_pendiente = 0
            self.ticks_invulnerabilidad = 0
            self.velocidad_gravedad = 0.10 # Valor base ajustado
        
        self.timer_gravedad = 0
        self.timer_id = None 

    def mostrar_menu_dificultad(self):
        self.canvas.delete("all")
        grid_size = self.datos_juego.get('config', {}).get('grid_size', [18, 18])
        ancho_centro = (grid_size[0] * self.taman_celda) / 2
        alto_centro = (grid_size[1] * self.taman_celda) / 2
        
        self.canvas.create_text(ancho_centro, alto_centro - 60, text="SELECCIONA DIFICULTAD", fill="white", font=("Arial", 16, "bold"))
        self.canvas.create_text(ancho_centro, alto_centro - 10, text="Presiona [1] - BABY (Facil)", fill="lightgreen", font=("Arial", 12, "bold"))
        self.canvas.create_text(ancho_centro, alto_centro + 20, text="Presiona [2] - ENTUSIASTA (Medio)", fill="yellow", font=("Arial", 12, "bold"))
        self.canvas.create_text(ancho_centro, alto_centro + 50, text="Presiona [3] - NYAN_CAT (Dificil)", fill="cyan", font=("Arial", 12, "bold"))

    def run(self):
        nivel_solicitado = self.datos_juego.get('nivel', 'SNAKE')
        
        if nivel_solicitado == 'MENU':
            self.mostrar_menu_dificultad()
        else:
            self.iniciar_con_dificultad(nivel_solicitado)
            
        self.root.mainloop()

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return

        self.timer_gravedad += 0.05 
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            
            # El power-up de estrella dura aproximadamente 50 ticks
            if self.tipo_juego == 'SNAKE' and self.ticks_invulnerabilidad > 0:
                self.ticks_invulnerabilidad -= 1
                
            self.ejecutar_evento('ON_TICK')

        self.dibujar()
        self.timer_id = self.root.after(self.velocidad, self.game_loop)
        
    def cerrar_ventana(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)

    def manejar_input_gui(self, event):
        tecla = event.keysym.upper()
        key = event.keysym.upper()
        
        if not self.juego_iniciado:
            if tecla in ['1', 'KP_1']:
                self.iniciar_con_dificultad('BABY')
            elif tecla in ['2', 'KP_2']:
                self.iniciar_con_dificultad('ENTUSIASTA')
            elif tecla in ['3', 'KP_3']:
                self.iniciar_con_dificultad('NYAN_CAT')
            return
            
        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        elif self.tipo_juego == 'SNAKE':
            if key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')

    def dibujar(self):
        self.canvas.delete("all") 
        
        # Efecto visual del Score cuando la estrella está activa
        if self.tipo_juego == 'SNAKE' and self.ticks_invulnerabilidad > 0:
            self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion) + "\n*INMUNE*", fg='yellow')
        else:
            self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion), fg='white')
        
        COLOR_GRID_FIJA = '#343434' 
        COLOR_PIEZA = '#00FFFF'     
        COLOR_SNAKE_CABEZA = '#00FF00' 
        COLOR_SNAKE_CUERPO = '#33CC33' 
        COLOR_FOOD = '#FF0000'       
        COLOR_POISON = '#808080'     # Gris
        COLOR_STAR = '#FFD700'       # Amarillo
        COLOR_OBSTACLE = '#8B0000'   # Rojo Oscuro para las Entidades Fijas
        
        # Para items y otras geometrias generales
        geometria_base = "RECTANGULAR"
        if self.shapes_geom:
            geometria_base = self.shapes_geom.values()[0]
        
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                     self.dibujar_celda(x, y, COLOR_GRID_FIJA)

        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.pieza_x + x_offset, self.pieza_y + y_offset, COLOR_PIEZA)
        
        if self.tipo_juego == 'SNAKE':
            # Dibujo de entidades
            if self.posicion_comida:
                self.dibujar_celda(self.posicion_comida[0], self.posicion_comida[1], COLOR_FOOD, "CIRCULAR")
            if self.posicion_veneno:
                self.dibujar_celda(self.posicion_veneno[0], self.posicion_veneno[1], COLOR_POISON, "TRIANGULAR")
            if self.posicion_estrella:
                self.dibujar_celda(self.posicion_estrella[0], self.posicion_estrella[1], COLOR_STAR, "TRIANGULAR")
            
            # Dibujo de Obstaculos fijos (Nivel Final)
            for obs_x, obs_y in self.posiciones_obstaculos:
                self.dibujar_celda(obs_x, obs_y, COLOR_OBSTACLE, "RECTANGULAR")

            # Dibujo del cuerpo
            colores_nyan = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3']
            
            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento
                if self.nivel == 'NYAN_CAT':
                    if i == 0:
                        self.dibujar_cabeza_gato(x, y) # La cabeza redonda con rasgos de gato
                    else:
                        color_elegido = random.choice(colores_nyan)
                        self.dibujar_celda(x, y, color_elegido, geometria_base)
                elif self.nivel in ['BABY', 'ENTUSIASTA']:
                    # Mantienen su geometria circular u original definida en el json
                    color_elegido = COLOR_SNAKE_CABEZA if i == 0 else COLOR_SNAKE_CUERPO
                    self.dibujar_celda(x, y, color_elegido, geometria_base)
                else:
                    # SNAKE Original siempre cuadrado
                    color_elegido = COLOR_SNAKE_CABEZA if i == 0 else COLOR_SNAKE_CUERPO
                    self.dibujar_celda(x, y, color_elegido, "RECTANGULAR")

    def dibujar_cabeza_gato(self, x, y):
        """Dibuja una cabeza de gato usando figuras geometricas basicas del Canvas"""
        ts = self.taman_celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        
        color_gato = '#DDDDDD' # Gris claro
        
        # Orejas (Poligonos)
        self.canvas.create_polygon(x1+2, y1+12, x1+12, y1+2, x1, y1, fill=color_gato, outline='#000000')
        self.canvas.create_polygon(x2-2, y1+12, x2-12, y1+2, x2, y1, fill=color_gato, outline='#000000')
        
        # Cabeza (Circulo principal)
        self.canvas.create_oval(x1+2, y1+4, x2-2, y2-2, fill=color_gato, outline='#000000')
        
        # Ojos (Cuadritos negros)
        self.canvas.create_rectangle(x1+6, y1+10, x1+10, y1+14, fill='black')
        self.canvas.create_rectangle(x2-10, y1+10, x2-6, y1+14, fill='black')
        
        # Nariz (Cuadrito rosa)
        self.canvas.create_rectangle(x1+11, y1+15, x2-11, y1+18, fill='#FF69B4')

    def dibujar_celda(self, x, y, color, geometria="RECTANGULAR"):
        ts = self.taman_celda 
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        
        if geometria == "CIRCULAR":
            self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline='#000000')
        elif geometria == "TRIANGULAR":
            self.canvas.create_polygon(x1 + ts/2.0, y1, x1, y2, x2, y2, fill=color, outline='#000000')
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')

    def ejecutar_evento(self, nombre_evento):
        if nombre_evento in self.datos_juego['events']:
            for accion in self.datos_juego['events'][nombre_evento]:
                verbo, objeto = accion.get('accion'), accion.get('objeto')
                
                if verbo == 'INCREASE_SCORE': self.puntuacion += int(objeto)
                if verbo == 'DECREASE_SCORE': self.puntuacion -= int(objeto)
                if verbo == 'SET_SCORE': self.puntuacion = int(objeto)
                if verbo == 'GAME_OVER': self.juego_terminado = True

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN': self.tetris_spawn_pieza()
                    if verbo == 'MOVE': self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE': self.tetris_rotar_pieza()
                
                if self.tipo_juego == 'SNAKE':
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.snake_spawn_jugador(accion)
                    if verbo == 'MOVE' and objeto == 'PLAYER': self.snake_mover_jugador()
                    if verbo == 'GROW': self.snake_crecer()

    def iniciar_con_dificultad(self, nivel):
        self.nivel = nivel
        self.root.title("BrickScript - " + self.tipo_juego + " (Nivel: " + self.nivel + ")")
        
        # Limpiamos las entidades anteriores por si se reinicia
        self.posicion_comida = None
        self.posicion_veneno = None
        self.posicion_estrella = None
        self.posiciones_obstaculos = []
        self.puntuacion = 0
        self.ticks_invulnerabilidad = 0
        
        # --- NUEVOS AJUSTES DE VELOCIDAD DEFINITIVOS ---
        # A menor "velocidad" y "velocidad_gravedad", mas rapido se mueve
        if self.nivel == 'BABY':
            self.velocidad = 100 
            self.velocidad_gravedad = 0.10
            self.canvas.config(bg="black")
            
        elif self.nivel == 'ENTUSIASTA':
            self.velocidad = 70 
            self.velocidad_gravedad = 0.10
            self.canvas.config(bg="black")
            
        elif self.nivel == 'NYAN_CAT':
            self.velocidad = 50 
            self.velocidad_gravedad = 0.10 # Mismo tick rate, pero al ser 50ms el base es menos frenetico que antes, pero el más rápido
            self.canvas.config(bg="darkblue")
            
        else: # SNAKE ORIGINAL
            self.velocidad = 100 
            self.velocidad_gravedad = 0.10
            self.canvas.config(bg="black")

        # Disparamos el evento inicial (lee el .brick)
        self.ejecutar_evento('ON_START')
        
        # Aseguramos que siempre haya al menos una comida inicial
        if self.tipo_juego == 'SNAKE':
            self.snake_spawn_entidad('FOOD')
            
            # Spawneamos items segun la dificultad
            if self.nivel in ['ENTUSIASTA', 'NYAN_CAT']:
                self.snake_spawn_entidad('POISON')
                self.snake_spawn_entidad('STAR')
                
            if self.nivel == 'NYAN_CAT':
                # Generamos 5 Entidades/Obstaculos fijos en el nivel final
                for _ in range(5):
                    self.snake_spawn_entidad('OBSTACLE')
        
        self.juego_iniciado = True
        self.canvas.delete("all")
        self.root.after(self.velocidad, self.game_loop)

    # --- LOGICA TETRIS ---
    def tetris_spawn_pieza(self):
        nombre_pieza = random.choice(self.datos_juego['shapes'].keys())
        self.pieza_actual = self.datos_juego['shapes'][nombre_pieza]
        self.pieza_x, self.pieza_y, self.pieza_rotacion = self.ancho / 2 - 2, 0, 0
        if self.tetris_verificar_colision(self.pieza_x, self.pieza_y, self.pieza_rotacion):
            self.juego_terminado = True

    def tetris_mover_pieza(self, direccion):
        if not self.pieza_actual: return
        dx, dy = 0, 0
        if direccion == 'LEFT': dx = -1
        elif direccion == 'RIGHT': dx = 1
        elif direccion == 'DOWN': dy = 1
        if not self.tetris_verificar_colision(self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy > 0:
            self.tetris_fijar_pieza()

    def tetris_rotar_pieza(self):
        if not self.pieza_actual: return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion

    def tetris_fijar_pieza(self):
        matriz_pieza = self.pieza_actual[self.pieza_rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    if 0 <= self.pieza_y + y_offset < self.alto and 0 <= self.pieza_x + x_offset < self.ancho:
                        self.grid[self.pieza_y + y_offset][self.pieza_x + x_offset] = 1
        self.pieza_actual = None
        self.tetris_limpiar_lineas()
        self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual: return False
        matriz_pieza = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nuevo_x, nuevo_y = x + x_offset, y + y_offset
                    if not (0 <= nuevo_x < self.ancho and 0 <= nuevo_y < self.alto and self.grid[nuevo_y][nuevo_x] == 0):
                        return True
        return False

    def tetris_limpiar_lineas(self):
        nuevo_grid = [fila for fila in self.grid if not all(fila)]
        lineas_limpias = self.alto - len(nuevo_grid)
        if lineas_limpias > 0:
            self.grid = [[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid
            for _ in range(lineas_limpias): self.ejecutar_evento('ON_LINE_CLEAR')

    # --- NUEVA LOGICA SNAKE ---
    def snake_spawn_jugador(self, accion):
        coords = accion['params'][0] if accion['params'] else [self.ancho / 2, self.alto / 2]
        self.serpiente_cuerpo = [(coords[0], coords[1])]
        self.serpiente_direccion = (1, 0)
        
    def snake_spawn_entidad(self, tipo):
        while True:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            # Evita que se genere sobre la serpiente o sobre un obstáculo existente
            if (x, y) not in self.serpiente_cuerpo and (x, y) not in self.posiciones_obstaculos:
                if tipo == 'FOOD': self.posicion_comida = (x, y)
                elif tipo == 'POISON': self.posicion_veneno = (x, y)
                elif tipo == 'STAR': self.posicion_estrella = (x, y)
                elif tipo == 'OBSTACLE': self.posiciones_obstaculos.append((x, y))
                break
                
    def snake_mover_jugador(self):
        if not self.serpiente_cuerpo: return
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)

        # 1. Colisiones con los Muros
        if not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto):
            if self.ticks_invulnerabilidad > 0: # Estrella activa: atraviesa paredes
                nueva_cabeza = (nueva_cabeza[0] % self.ancho, nueva_cabeza[1] % self.alto)
            else:
                self.juego_terminado = True
                return
            
        # 2. Colision consigo misma (Canibalismo)
        if nueva_cabeza in self.serpiente_cuerpo[:-1]:
            if self.ticks_invulnerabilidad <= 0:
                self.juego_terminado = True
                return

        # 3. Colisiones con Entidades Fijas (Obstaculos en Nivel Final)
        if nueva_cabeza in self.posiciones_obstaculos:
            if self.ticks_invulnerabilidad <= 0:
                if self.puntuacion > 0:
                    self.puntuacion = 0 # Pierde todos los puntos, pero sigue vivo
                else:
                    self.juego_terminado = True # Si no tiene puntos, Game Over
                    return

        # Mueve la cabeza
        self.serpiente_cuerpo.insert(0, nueva_cabeza)
        
        # 4. Manejo de Items Interactivos
        if nueva_cabeza == self.posicion_comida:
            self.ejecutar_evento('ON_EAT_FOOD') # Ejecuta el sonido o puntos base si hay
            self.posicion_comida = None
            self.snake_spawn_entidad('FOOD')    # Spawnea la siguiente comida
            
        elif self.posicion_veneno and nueva_cabeza == self.posicion_veneno:
            if self.ticks_invulnerabilidad <= 0:
                self.puntuacion -= 10
                if self.puntuacion <= 0: # Si los puntos llegan a 0 o bajan de cero, pierde
                    self.juego_terminado = True
            self.posicion_veneno = None
            self.snake_spawn_entidad('POISON')
                
        elif self.posicion_estrella and nueva_cabeza == self.posicion_estrella:
            self.ticks_invulnerabilidad = 50 # 5 Segundos aprox de invulnerabilidad
            self.posicion_estrella = None
            self.snake_spawn_entidad('STAR')

        # 5. Crecimiento de la serpiente
        if self.crecer_pendiente > 0:
            self.crecer_pendiente -= 1
        else:
            self.serpiente_cuerpo.pop()

    def snake_cambiar_direccion(self, direccion):
        if direccion == 'UP' and self.serpiente_direccion[1] != 1:
            self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN' and self.serpiente_direccion[1] != -1:
            self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT' and self.serpiente_direccion[0] != 1:
            self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1:
            self.serpiente_direccion = (1, 0)

    def snake_crecer(self):
        self.crecer_pendiente += 1

    def mostrar_game_over(self):
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Uso: python runtime.py <archivo_juego.json>"
        sys.exit(1)
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f:
            datos_juego = json.load(f)
    except IOError:
        print "Error: No se pudo encontrar el archivo " + archivo_juego
        sys.exit(1)
    juego = Juego(datos_juego)
    juego.run()