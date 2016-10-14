import tkinter
import serial
import sys
import numpy as np
import struct
import threading

class UARTConection():
	
	def __init__( self , port = 'COM4' , baudrate = 115200 ):
		
		self.socket = serial.Serial( port = port , baudrate = baudrate )
		
	def ReadBytes( self , byte_size ):
		
		data = np.zeros( (byte_size) , dtype=np.uint8 )
		
		for pos in range( byte_size ):
			read = self.socket.read()
			if read == b'':
				return data
			data[pos] = struct.unpack('B', read )[0]
		
		return data
		
	def Close( self ):
		
		self.socket.close()

class Screen():
	
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
		
	def Loop( self ):
		
		self.screen.mainloop()

class UARTConection_Screen( threading.Thread ):
	
	def __init__( self , conection , screen ):
		
		self.uartConection = conection
		self.screen = screen
		
		screen_pixel_size = (self.screen.width + 1) * (self.screen.height + 1)
		if screen_pixel_size % 8 != 0:
			self.recive_size = int(screen_pixel_size / 8) + 1
		else:
			self.recive_size = int(screen_pixel_size / 8)
		
	def Loop( self ):
		
		threading.Thread.__init__( self )
		self.start()
		
	def run( self ):
		
		while True:
			self.Recive_and_show()
		
	def PrintScreen( self , packScreen , fileName='none' ):
		
		try:
			
			sys_stdout = sys.stdout
			output = open( fileName , 'w' )
			if fileName != 'none':
				sys.stdout = output
			
			counter = 0
			
			for itePackScreen in packScreen:
				
				for pos in reversed(range(8)):
					
					if( itePackScreen & (1 << pos) ):
						sys.stdout.write( '1' )
					else:
						sys.stdout.write( '0' )
					
					counter = counter + 1
					if counter > (self.screen.width + 1):
						sys.stdout.write( '\n' )
						sys.stdout.flush()
						counter = 0
			
		finally:
			
			sys.stdout = sys_stdout
			output.close()
		
	def Recive_and_show( self ):
		
		try:
			
			recive = self.uartConection.ReadBytes( self.recive_size )
			#~ self.PrintScreen( recive , 'Screen.txt' )
			self.screen.Show(recive)
			
		except RuntimeError:
			print("The screen is closed")


try:
	
	conect = UARTConection()
	
	pixel_size = 20
	width = int( 1366 / pixel_size ) # 68
	height = int( 700 / pixel_size ) # 35
	#~ width = 5
	#~ height = 5
	screen = Screen( width-1 , height-1 , pixel_size )
	
	intercomunicator = UARTConection_Screen( conect , screen )
	intercomunicator.Loop();
	screen.Loop()
	
finally:
	
	conect.Close()
