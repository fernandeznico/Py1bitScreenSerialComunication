import tkinter
import serial
import sys
import numpy as np
import struct
import threading

class UARTConection():
	
	def __init__( self , port = 'COM4' , baudrate = 115200 ):
		
		self.socket = serial.Serial( port = port , baudrate = baudrate )
		
	def ReadBits( self , byte_size ):
		
		data = np.zeros( (byte_size) , dtype=np.uint8 )
		
		for pos in range( byte_size ):
			#data[pos] = self.socket.read()
			data[pos] = struct.unpack('B', self.socket.read() )[0]
		
		return data
		
	def Close( self ):
		
		self.socket.close()

class Screen( threading.Thread ):
	
	def __init__( self ,
				  width = 100 ,
				  height = 70 ,
				  pixel_size = 8 ,
				  pixel_color = "black" ,
				  background = "white" ):
		
		self.buff = {}
		
		self.width = width
		self.height = height
		self.pixel_size = pixel_size
		self.pixel_color = pixel_color
		self.background = background
		
		self.window = tkinter.Tk()
		# Thread
		self.window.protocol( "WM_DELETE_WINDOW" , self.callback )
		# Pixel can see from (3,3) to (real_width,real_height)
		self.real_width = self.width * self.pixel_size + self.pixel_size + 3
		# Pixel can see from (3,3) to (real_width,real_height)
		self.real_height = self.height * self.pixel_size + self.pixel_size + 3
		self.screen = tkinter.Canvas( self.window ,
									  bg = self.background ,
									  height = self.real_height ,
									  width = self.real_width )
		self.screen.pack()
		self.window.update()
		
		threading.Thread.__init__( self )
		self.start()
		
	def run( self ):
		
		self.window.mainloop()
		
	def callback(self): # Thread
		
		self.window.quit()
		
	def CreatePixel( self , x , y ):
		
		if (x,y) in self.buff:
			return
		
		if x > self.width:
			return
		
		if y > self.height:
			return
		
		real_x = (x * self.pixel_size) + 3 # Pixel can see from (3,3) to (real_width,real_height)
		real_y = (y * self.pixel_size) + 3 # Pixel can see from (3,3) to (real_width,real_height)
		
		rect = self.screen.create_rectangle( real_x ,
											 real_y ,
											 real_x + self.pixel_size ,
											 real_y + self.pixel_size ,
											 fill = self.pixel_color ,
											 outline = self.pixel_color )
		
		self.buff[(x,y)] = rect
		
	def ErasePixel( self , x , y ):
		
		if (x,y) not in self.buff:
			return
		
		self.screen.delete( self.buff[(x,y)] )
		del self.buff[(x,y)]
		
	def Clear( self ):
		
		self.screen.delete("all")
		
	def Update( self ):
		
		self.window.update()
		
	def Show( self , vect ):
		
		pack_size = 8 #np.uint8
		
		packs_float = self.width * self.height / pack_size
		packs = int(packs_float)
		if packs < packs_float :
			packs = packs + 1
		
		if len(vect) < packs:
			print( "Screen size: Fault" )
		
		#self.Clear()
		
		x = 0
		y = 0
		for vectIte in vect:
			for i in reversed(range( 0 , pack_size )): # Read bit7 first (left to right)
				
				if (1<<i) & vectIte:
					self.CreatePixel( x , y )
				else:
					self.ErasePixel( x , y )
				
				x = x + 1
				if x == self.width + 1 :
					y = y + 1
					x = 0
		
		self.screen.pack()
		self.Update()

try:
	
	pixel_size = 80
	#~ width = int( 1366 / pixel_size ) # 68
	#~ height = int( 700 / pixel_size ) # 35
	width = 5
	height = 5
	screen_pixel_size = width * height
	if screen_pixel_size % 8 != 0:
		recive_size = int(screen_pixel_size / 8) + 1
	else:
		recive_size = int(screen_pixel_size / 8)
	conect = UARTConection()
	screen = Screen(width-1,height-1,pixel_size)
	
	while True:
		recive = conect.ReadBits(recive_size)
		#~ print(recive)
		screen.Show(recive)
	
except RuntimeError:
	
	print("The screen is closed")
	
finally:
	
	conect.Close()
