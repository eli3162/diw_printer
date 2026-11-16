_K='command'
_J='Backward'
_I='backward'
_H='Forward'
_G='forward'
_F='set_pos'
_E='linear_move'
_D=True
_C=False
_B='f'
_A=None
import asyncio,math,re,time,machine
gcode_spec_list={'G0':_E,'G1':_E,'G2':'clockwise_arc','G3':'counterclockwise_arc','G4':'dwell','G10':'retract_filament','G11':'unretract_filament','G20':'units_inch','G21':'units_mm','G28':'home','G90':'absolute_pos','G91':'relative_pos','G92':_F,'M0':'stop','M1':'sleep','M2':'prgm_end','M3':'clockwise_spindle_on','M4':'counterclockwise_spindle_on','M5':'spindle_off','M18':'disable_motors','M20':'list_sd','M21':'init_sd','M22':'deinit_sd','M23':'select_sd','M24':'start_sd_pr"int','M25':'pause_sd_print','M26':'pos_sd','M27':'check_sd','M28':'start_sd_write','M29':'stop_sd_write','M30':'delete_sd_file','M32':'start_sd_file_print','M42':'set_pin','M82':'absolute_extruder','M83':'relative_extruder','M84':'disable_idle_hold','M104':'set_extruder_temp','M105':'get_extruder_temp','M106':'fan_on','M107':'fan_off','M108':'bed_heating_off','M109':'extruder_heat_wait','M112':'emergency_stop','M114':'get_pos','M115':'get_firmware','M140':'fast_bed_heating','M150':'led_color','M190':'wait_bed_heating','M300':'beep'}
class MachineError(Exception):0
class StepperMotor:
	def __init__(A,enable_pin,step_pin,dir_pin,steps_per_turn=200,deinit_when_off=_D):A.enable_pin=enable_pin;A.step_pin=step_pin;A.dir_pin=dir_pin;A.steps_per_turn=steps_per_turn;A.control_pins={A.enable_pin:machine.Pin(A.enable_pin,machine.Pin.OUT,value=1),A.step_pin:machine.Pin(A.step_pin,machine.Pin.OUT,value=0),A.dir_pin:machine.Pin(A.dir_pin,machine.Pin.OUT,value=0)};A.control_state=_C;A.deinit_when_off=deinit_when_off
	def digital_write(A,pin,value):A.control_pins[pin].value(value)
	def start(A):A.digital_write(A.enable_pin,0)
	def stop(A,override=_C):
		if A.deinit_when_off or override:A.digital_write(A.enable_pin,1)
	def set_direction(A,dir):A.digital_write(A.dir_pin,dir)
	def step(A,time):A.digital_write(A.step_pin,1);A.digital_write(A.step_pin,0)
	def stop_timer(A,time=0):
		if A.control_state:
			try:A.freq_timer.deinit();A.deinit_timer.deinit()
			except:A.control_state=_C
	def stop_turn(A):A.stop_timer();A.stop()
	async def step_turn(A,steps,freq,direction=_A):
		D=freq;C=direction;B=steps
		if C in[_G,_H,1,_D,_B]:A.set_direction(1)
		elif C in[_I,_J,0,_C,'b']:A.set_direction(0)
		elif C==_A:0
		else:raise ValueError(f"Invalid Direction: {C}")
		if C is _A or B<0:
			if B>0:A.set_direction(1)
			elif B<0:A.set_direction(0);B=-1*B
			else:return
		try:A.start();A.freq_timer=machine.Timer(-1);A.deinit_timer=machine.Timer(-1);A.freq_timer.init(mode=machine.Timer.PERIODIC,freq=D,callback=A.step);A.deinit_timer.init(mode=machine.Timer.ONE_SHOT,period=round(1000*B/D),callback=A.stop_timer);A.control_state=_D;await asyncio.sleep(B/D);A.stop()
		except KeyboardInterrupt:A.stop_timer();A.stop()
	def start_step_turn(A,steps,freq,direction=_A):
		C=direction;B=steps
		if C in[_G,_H,1,_D,_B]:A.set_direction(1)
		elif C in[_I,_J,0,_C,'b']:A.set_direction(0)
		elif C==_A:0
		else:raise ValueError(f"Invalid Direction: {C}")
		if C is _A or B<0:
			if B>0:A.set_direction(1)
			elif B<0:A.set_direction(0);B=-1*B
			else:return
		A.start();A.freq_timer=machine.Timer(-1);A.freq_timer.init(mode=machine.Timer.PERIODIC,freq=freq,callback=A.step);A.control_state=_D
	async def turn(A,degrees,time,direction=_A):
		B=degrees
		if B:C=math.floor(B/360*A.steps_per_turn);await A.step_turn(C,C/time,direction);return
		else:return
	def start_turn(A,degrees,direction=_A):
		B=degrees
		if B:D=1;C=math.floor(B/360*A.steps_per_turn);A.start_step_turn(C,C/D,direction);return
		else:return
	def turn_step(A,degrees,time,direction):asyncio.run(A.turn(degrees,time,direction=direction))
	def signed_turn(C,signed_degrees,time):
		A=signed_degrees
		if A>0:B=1
		if A<0:B=0
		else:raise MachineError('Unsigned degrees not acceptable for function signed_turn()')
		D=abs(A);asyncio.run(C.turn(D,time,direction=B))
	def lock(A):A.deinit_when_off=_C;A.start()
	def unlock(A):A.deinit_when_off=_D;A.stop()
class EndButton:
	def __init__(A,pin):A.pin_obj=machine.Pin(pin,machine.Pin.IN,machine.Pin.PULL_UP)
	def state(A):
		if A.pin_obj.value()==0:return _C
		return A.pin_obj.value()==1
def gcode_parse(inputdata):
	A=inputdata
	if not isinstance(A,tuple):
		if isinstance(A,str):A=tuple([A])
		elif isinstance(A,list):A=tuple(A)
	G=[]
	for B in A:
		if';'in B:B=B.split(';',1)[0]
		if'('in B and')'in B:B=re.sub('\\(.*?\\)','',B)
		D=B.split(' ')
		while''in D:D.remove('')
		if D:
			E=D.pop(0).upper();I=D;F={}
			for C in I:
				if"'"in C[1:]or'"'in C[1:]:F[C[:1].lower()]=C[1:]
				else:F[C[:1].lower()]=float(C[1:])
			if E or F:
				if E in gcode_spec_list:H=gcode_spec_list[E]
				else:H='Not Implemented'
				G.append({_K:E,'name':H,'args':F})
	return G
class Extruder:
	def __init__(A,extruder_motor,ratio=1):A.extruder_motor=extruder_motor;A.extrude_ratio=ratio;A.steps_per_turn=360/1.8
	async def extrude(A,mm,time,direction=_A):
		if mm:C=360*mm;B=math.floor(C/360*A.steps_per_turn*A.extrude_ratio);await A.extruder_motor.step_turn(B,B/time,direction);return
		else:return
class Printer:
	def __init__(A,x_motor,y_motor,z_motor,x_limit=_A,y_limit=_A,z_limit=_A,main_extruder=_A,secondary_extruder=_A,auxilarry_extruder=_A):
		G=z_limit;F=y_limit;E=x_limit;D=auxilarry_extruder;C=secondary_extruder;B=main_extruder;A.x_motor=x_motor;A.y_motor=y_motor;A.z_motor=z_motor
		if E:A.x_limit=E
		if F:A.y_limit=F
		if G:A.z_limit=G
		if B or C or D:A.extruder_set={'main':B,'secondary':C,'auxilarry':D}
		[A.main_extruder,A.secondary_extruder,A.auxillary_extruder]=B,C,D;A.pos={'x':0,'y':0,'z':0};A.last_feed_rate=0
	def writeSerial(A):print(f"send:{A}")
	def setpos(A,x=_A,y=_A,z=_A):
		if not x is _A:A.pos['x']=x
		if not y is _A:A.pos['y']=y
		if not z is _A:A.pos['z']=z
	def signed_direction(C,angle):
		A=angle
		if A>0:B=1
		if A<=0:B=0
		return[abs(A),B]
	async def movetorelative(A,time=_A,speed=_A,x=0,y=0,z=0,e=_A):
		D=time;C=speed;H=360/(16*math.pi);I=360/8;E=x*H;F=y*H;G=z*I;[E,J]=A.signed_direction(E);[F,K]=A.signed_direction(F);[G,L]=A.signed_direction(G);[M,N]=A.signed_direction(e)
		if D and C:raise MachineError('User may not choose both time and speed inputs')
		elif D:B=D
		elif C:
			O=math.sqrt(x**2+y**2+z**2);B=O/C
			if B==0 and e:B=e/C
		else:raise MachineError('User speed or time not specified')
		[P,Q,R]=[A.pos['x']+x,A.pos['y']+y,A.pos['z']+z];A.setpos(x=P,y=Q,z=R);await asyncio.gather(A.x_motor.turn(E,B,direction=J),A.y_motor.turn(F,B,direction=K),A.z_motor.turn(G,B,direction=L),A.main_extruder.extrude(M,B,direction=N))
	def getpos(A):return A.pos['x'],A.pos['y'],A.pos['z']
	async def asyncmovetopoint(A,point,time=_A,speed=_A):[B,C,D]=A.getpos();[E,F,G,H]=point;I=E-B,F-C,G-D;[J,K,L]=I;await A.movetorelative(time=time,speed=speed,x=J,y=K,z=L,e=H)
	def moveto(A,time=_A,speed=_A,x=_A,y=_A,z=_A,e=_A):
		B=speed
		if x is _A:x=A.pos['x']
		if y is _A:y=A.pos['y']
		if z is _A:z=A.pos['z']
		if e is _A:e=0
		C=x,y,z,e
		if time or B:asyncio.run(A.asyncmovetopoint(C,time=time,speed=B))
	def software_home(A):A.moveto(speed=100,x=0,y=0,z=0)
	def wait(A,p=0,s=0):time.sleep(p/1000+s)
	def runcodeline(B,parsed_gcode):
		E=parsed_gcode;D='speed';C=E['name'];F=E[_K];A=E['arguments'];A[_B]=A[_B]/60
		if C==_E:
			if _B in A:A[D]=A[_B];B.last_feed_rate=A[_B];A.pop(_B)
			elif B.last_feed_rate:A[D]=B.last_feed_rate
			else:A[D]=150
			if B.speed_override:A[D]=B.speed_override
			B.moveto(**A)
		elif C=='home':B.hone_axis()
		elif C==_F:
			if'e'in A:A.pop('e')
			B.setpos(**A)
		elif C=='dwell':B.wait(**A)
		else:print(f"Error: No implementation found for gcode {F}, name {C}.")
	def run_gcode(A,gcode):
		B=gcode_parse(gcode)
		for C in B:A.runcodeline(C)
	def hone_axis(A):0
	def lock(A):A.x_motor.lock();A.y_motor.lock();A.z_motor.lock()
	def unlock(A):A.x_motor.unlock();A.y_motor.unlock();A.z_motor.unlock()
def initPrinter(setpins=_A):
	P='z_limit';O='y_limit';N='x_limit';M=setpins;L='z_motor';K='y_motor';J='x_motor';I='extruder_auxilarry';H='extruder_secondary';G='extruder_main';F='pin';E='ratio';D='dir';C='step';B='en'
	if not M is _A:A=M
	else:A={J:{B:0,C:1,D:2},K:{B:3,C:4,D:5},L:{B:6,C:7,D:8},G:{B:9,C:10,D:11,E:1},H:{B:12,C:13,D:14,E:1},I:{B:15,C:16,D:17,E:1},N:{F:21},O:{F:22},P:{F:26},'aux':{'sda':23,'scl':24,'pwm':25}}
	Q=StepperMotor(enable_pin=A[J][B],step_pin=A[J][C],dir_pin=A[J][D]);R=StepperMotor(enable_pin=A[K][B],step_pin=A[K][C],dir_pin=A[K][D]);S=StepperMotor(enable_pin=A[L][B],step_pin=A[L][C],dir_pin=A[L][D]);T=StepperMotor(enable_pin=A[G][B],step_pin=A[G][C],dir_pin=A[G][D]);U=StepperMotor(enable_pin=A[H][B],step_pin=A[H][C],dir_pin=A[H][D]);V=StepperMotor(enable_pin=A[I][B],step_pin=A[I][C],dir_pin=A[I][D]);W=Extruder(T,ratio=A[G][E]);X=Extruder(U,ratio=A[H][E]);Y=Extruder(V,ratio=A[I][E]);Z=EndButton(pin=A[N][F]);a=EndButton(pin=A[O][F]);b=EndButton(pin=A[P][F]);c=Printer(Q,R,S,Z,a,b,W,X,Y);return c
def syringenozzle(nozzle_diameter=1.5,syringe_diameter=10.5,screw_pitch=2):return screw_pitch*(nozzle_diameter**2/syringe_diameter**2)