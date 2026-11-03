_I='Backward'
_H='backward'
_G='Forward'
_F='forward'
_E='args'
_D='command'
_C=True
_B=False
_A=None
import asyncio,math,re,machine
class MachineError(Exception):0
class StepperMotor:
	def __init__(self,enable_pin,step_pin,dir_pin,steps_per_turn=200):self.enable_pin=enable_pin;self.step_pin=step_pin;self.dir_pin=dir_pin;self.steps_per_turn=steps_per_turn;self.control_pins={self.enable_pin:machine.Pin(self.enable_pin,machine.Pin.OUT,value=1),self.step_pin:machine.Pin(self.step_pin,machine.Pin.OUT,value=0),self.dir_pin:machine.Pin(self.dir_pin,machine.Pin.OUT,value=0)};self.control_state=_B
	def digital_write(self,pin,value):self.control_pins[pin].value(value)
	def start(self):self.digital_write(self.enable_pin,0)
	def stop(self):self.digital_write(self.enable_pin,1)
	def set_direction(self,dir):self.digital_write(self.dir_pin,dir)
	def step(self,time):self.digital_write(self.step_pin,1);self.digital_write(self.step_pin,0)
	def stop_timer(self,time=0):
		if self.control_state:self.freq_timer.deinit();self.deinit_timer.deinit();self.control_state=_B
	def stop_turn(self):self.stop();self.stop_timer()
	async def step_turn(self,steps,freq,direction=_A):
		if direction in[_F,_G,1,_C,'f']:self.set_direction(1)
		elif direction in[_H,_I,0,_B,'b']:self.set_direction(0)
		elif direction==_A:0
		else:raise ValueError(f"Invalid Direction: {direction}")
		if direction is _A or steps<0:
			if steps>0:self.set_direction(1)
			elif steps<0:self.set_direction(0);steps=-1*steps
			else:return
		try:self.start();self.freq_timer=machine.Timer(-1);self.deinit_timer=machine.Timer(-1);self.freq_timer.init(mode=machine.Timer.PERIODIC,freq=freq,callback=self.step);self.deinit_timer.init(mode=machine.Timer.ONE_SHOT,period=round(1000*steps/freq),callback=self.stop_timer);self.control_state=_C;await asyncio.sleep(steps/freq);self.stop()
		except KeyboardInterrupt:
			self.stop_timer(0);self.stop()
			try:
				if self.control_state:self.freq_timer.deinit();self.deinit_timer.deinit();self.control_state=_B
			except Exception:pass
	def start_step_turn(self,steps,freq,direction=_A):
		if direction in[_F,_G,1,_C,'f']:self.set_direction(1)
		elif direction in[_H,_I,0,_B,'b']:self.set_direction(0)
		elif direction==_A:0
		else:raise ValueError(f"Invalid Direction: {direction}")
		if direction is _A or steps<0:
			if steps>0:self.set_direction(1)
			elif steps<0:self.set_direction(0);steps=-1*steps
			else:return
		self.start();self.freq_timer=machine.Timer(-1);self.freq_timer.init(mode=machine.Timer.PERIODIC,freq=freq,callback=self.step);self.control_state=_C
	async def turn(self,degrees,time,direction=_A):
		if degrees:steps=math.floor(degrees/360*self.steps_per_turn);await self.step_turn(steps,steps/time,direction);return
		else:return
	def start_turn(self,degrees,direction=_A):
		if degrees:time=1;steps=math.floor(degrees/360*self.steps_per_turn);self.start_step_turn(steps,steps/time,direction);return
		else:return
	def turn_step(self,degrees,time,direction):asyncio.run(self.turn(degrees,time,direction=direction))
	def signed_turn(self,signed_degrees,time):
		if signed_degrees>0:direction=1
		if signed_degrees<0:direction=0
		else:raise MachineError('Unsigned degrees not acceptable for function signed_turn()')
		degrees=abs(signed_degrees);asyncio.run(self.turn(degrees,time,direction=direction))
class EndButton:
	def __init__(self,pin):self.pin_obj=machine.Pin(pin,machine.Pin.IN,machine.Pin.PULL_UP)
	def state(self):
		if self.pin_obj.value()==0:return _B
		return self.pin_obj.value()==1
class GCodeParser:
	def __init__(self,matchlist=_A):
		if matchlist:self.matchlist=matchlist
		else:self.matchlist={}
	def parseline(self,line):
		if';'in line:line=line.split(';',1)[0]
		if'('in line and')'in line:line=re.sub('\\(.*?\\)','',line)
		phrases=line.split(' ')
		while''in phrases:phrases.remove('')
		try:
			if phrases:
				command=phrases.pop(0).upper();raw_arguments=phrases;arguments={}
				for argument in raw_arguments:
					if"'"in argument[1:]or'"'in argument[1:]:arguments[argument[:1].lower()]=argument[1:]
					else:arguments[argument[:1].lower()]=float(argument[1:])
				if command in self.matchlist:command=self.matchlist[command]
				return{_D:command,_E:arguments}
		except Exception:pass
		return{_D:'',_E:{}}
	def parse(self,inputdata):
		if isinstance(inputdata,str):
			if inputdata.count('\n')>1:inputdata=inputdata.splitlines()
			else:return self.parseline(inputdata)
		if isinstance(inputdata,list):
			output=[]
			for line in inputdata:
				parsedline=self.parseline(line)
				if parsedline!={_D:'',_E:{}}:output.append(parsedline)
			return output
class Extruder:
	def __init__(self,extruder_motor,ratio=1):self.extruder_motor=extruder_motor;self.extrude_ratio=ratio;self.steps_per_turn=360/1.8
	async def extrude(self,mm,time,direction=_A):
		if mm:degrees=360*mm;steps=math.floor(degrees/360*self.steps_per_turn*self.extrude_ratio);await self.extruder_motor.step_turn(steps,steps/time,direction);return
		else:return
class Printer:
	def __init__(self,x_motor,y_motor,z_motor,x_limit=_A,y_limit=_A,z_limit=_A,main_extruder=_A,secondary_extruder=_A,auxilarry_extruder=_A):
		self.x_motor=x_motor;self.y_motor=y_motor;self.z_motor=z_motor
		if x_limit:self.x_limit=x_limit
		if y_limit:self.y_limit=y_limit
		if z_limit:self.z_limit=z_limit
		if main_extruder or secondary_extruder or auxilarry_extruder:self.extruder_set={'main':main_extruder,'secondary':secondary_extruder,'auxilarry':auxilarry_extruder}
		[self.main_extruder,self.secondary_extruder,self.auxillary_extruder]=main_extruder,secondary_extruder,auxilarry_extruder;self.pos={'x':0,'y':0,'z':0};self.matchlist=_A;self.gcodeparser=GCodeParser(matchlist=self.matchlist);self.last_feed_rate=0
	def writeSerial(message):print(f"send:{message}")
	def setpos(self,x=_A,y=_A,z=_A):
		if not x is _A:self.pos['x']=x
		if not y is _A:self.pos['y']=y
		if not z is _A:self.pos['z']=z
	def signed_direction(self,angle):
		if angle>0:direction=1
		if angle<=0:direction=0
		return[abs(angle),direction]
	async def movetorelative(self,time=_A,speed=_A,x=0,y=0,z=0,e=_A):
		horizontal_conversion_const=360/(16*math.pi);vertical_conversion_const=360/8;y=-y;x_degrees=x*horizontal_conversion_const;y_degrees=y*horizontal_conversion_const;z_degrees=z*vertical_conversion_const;[x_degrees,x_direction]=self.signed_direction(x_degrees);[y_degrees,y_direction]=self.signed_direction(y_degrees);[z_degrees,z_direction]=self.signed_direction(z_degrees)
		if time and speed:raise MachineError('User may not choose both time and speed inputs')
		elif time:runtime=time
		elif speed:
			distance=math.sqrt(x**2+y**2+z**2);runtime=distance/speed
			if runtime==0 and e:runtime=e/speed
		else:raise MachineError('User speed or time not specified')
		await asyncio.gather(self.x_motor.turn(x_degrees,runtime,direction=x_direction),self.y_motor.turn(y_degrees,runtime,direction=y_direction),self.z_motor.turn(z_degrees,runtime,direction=z_direction),self.main_extruder.extrude(e,runtime,direction=0))
	def getpos(self):return self.pos['x'],self.pos['y'],self.pos['z']
	async def asyncmovetopoint(self,point,time=_A,speed=_A):[start_x,start_y,start_z]=self.getpos();[end_x,end_y,end_z,extrude]=point;movement_vector=end_x-start_x,end_y-start_y,end_z-start_z;[x,y,z]=movement_vector;self.setpos(x=end_x,y=end_y,z=end_z);await self.movetorelative(time=time,speed=speed,x=x,y=y,z=z,e=extrude)
	def moveto(self,time=_A,speed=_A,x=_A,y=_A,z=_A,e=_A):
		if x is _A:x=self.pos['x']
		if y is _A:y=self.pos['y']
		if z is _A:z=self.pos['z']
		if e is _A:e=0
		point=x,y,z,e
		if time or speed:asyncio.run(self.asyncmovetopoint(point,time=time,speed=speed))
	def software_home(self):self.moveto(speed=100,x=0,y=0,z=0)
	def runcodeline(self,pycode):
		A='speed';command=pycode[_D];arguments=pycode[_E]
		if command in'G0':arguments[A]=150;self.moveto(**arguments)
		elif command in'G1':
			if'f'in arguments:arguments[A]=arguments['f'];self.last_feed_rate=arguments['f'];arguments.pop('f')
			elif self.last_feed_rate:arguments[A]=self.last_feed_rate
			else:arguments[A]=150
			if self.speed_override:arguments[A]=10
			self.moveto(**arguments)
		elif command in'G28':self.hone_axis()
		elif command in'G92':
			if'e'in arguments:arguments.pop('e')
			self.setpos(**arguments)
	def run_gcode(self,gcode):
		parsed_gcode=self.gcodeparser.parse(gcode)
		if isinstance(parsed_gcode,list):
			for line in parsed_gcode:self.runcodeline(line)
		else:self.runcodeline(parsed_gcode)
	def hone_axis(self):0
def initPrinter(setpins=_A):
	N='z_limit';M='y_limit';L='x_limit';K='z_motor';J='y_motor';I='x_motor';H='extruder_auxilarry';G='extruder_secondary';F='extruder_main';E='pin';D='ratio';C='dir';B='step';A='en'
	if not setpins is _A:pins=setpins
	else:pins={I:{A:0,B:1,C:2},J:{A:3,B:4,C:5},K:{A:6,B:7,C:8},F:{A:9,B:10,C:11,D:1},G:{A:12,B:13,C:14,D:1},H:{A:15,B:16,C:17,D:1},L:{E:21},M:{E:22},N:{E:26},'aux':{'sda':23,'scl':24,'pwm':25}}
	x_motor=StepperMotor(enable_pin=pins[I][A],step_pin=pins[I][B],dir_pin=pins[I][C]);y_motor=StepperMotor(enable_pin=pins[J][A],step_pin=pins[J][B],dir_pin=pins[J][C]);z_motor=StepperMotor(enable_pin=pins[K][A],step_pin=pins[K][B],dir_pin=pins[K][C]);extruder_main_motor=StepperMotor(enable_pin=pins[F][A],step_pin=pins[F][B],dir_pin=pins[F][C]);extruder_secondary_motor=StepperMotor(enable_pin=pins[G][A],step_pin=pins[G][B],dir_pin=pins[G][C]);extruder_auxilarry_motor=StepperMotor(enable_pin=pins[H][A],step_pin=pins[H][B],dir_pin=pins[H][C]);extruder_main=Extruder(extruder_main_motor,ratio=pins[F][D]);extruder_secondary=Extruder(extruder_secondary_motor,ratio=pins[G][D]);extruder_auxilarry=Extruder(extruder_auxilarry_motor,ratio=pins[H][D]);x_button=EndButton(pin=pins[L][E]);y_button=EndButton(pin=pins[M][E]);z_button=EndButton(pin=pins[N][E]);printer=Printer(x_motor,y_motor,z_motor,x_button,y_button,z_button,extruder_main,extruder_secondary,extruder_auxilarry);return printer
def syringenozzle(nozzle_diameter=1.5,syringe_diameter=10.5,screw_pitch=2):return screw_pitch*(nozzle_diameter**2/syringe_diameter**2)
