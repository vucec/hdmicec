# -*- coding: utf-8 -*-

# maintainer: <info@vuplus-support.org>

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.

import struct
from enigma import eActionMap, eHdmiCEC
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap,NumberActionMap
from Components.config import config, getConfigListEntry, ConfigInteger, ConfigSubsection, ConfigSelection, ConfigText, ConfigYesNo, NoSave, ConfigNothing
from Components.ConfigList import ConfigListScreen
from Components.InputDevice import iInputDevices
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools import Notifications
from HdmiCec import HdmiCec
from os import system
import logging

import inspect

def lineno():
    """Returns current line number in plugin.py"""
    return "P%03d  " % inspect.currentframe().f_back.f_lineno

hdmi_cec = HdmiCec()

class HdmiCecPlugin(Screen,ConfigListScreen):
	skin = """
		<screen name="HDMICEC" position="center,center" size="700,400" title="VTI HDMI-CEC Plugin" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ececec" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ececec" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ececec" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ececec" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" zPosition="2" position="5,50" size="650,300" scrollbarMode="showOnDemand" transparent="1" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)

		config.hdmicec.input_address = ConfigText(default = "0", visible_width = 50, fixed_size = False)
		config.hdmicec.input_value1 = ConfigText(default = "0", visible_width = 50, fixed_size = False)
		config.hdmicec.input_value2 = ConfigText(default = "", visible_width = 50, fixed_size = False)
		config.hdmicec.input_value3 = ConfigText(default = "", visible_width = 50, fixed_size = False)
		config.hdmicec.input_value4 = ConfigText(default = "", visible_width = 50, fixed_size = False)
		config.hdmicec.avvolup = NoSave(ConfigNothing())
		config.hdmicec.avvoldown = NoSave(ConfigNothing())
		config.hdmicec.avvolmute = NoSave(ConfigNothing())
		config.hdmicec.avpwroff = NoSave(ConfigNothing())
		config.hdmicec.avpwron = NoSave(ConfigNothing())
		config.hdmicec.tvpwroff = NoSave(ConfigNothing())
		config.hdmicec.tvpwron = NoSave(ConfigNothing())
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Connect"))
		self["key_blue"] = StaticText(_("Disconnect"))
		self["shortcuts"] = ActionMap(["ShortcutActions", "SetupActions", "NumberActions" ],
		{
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyConnect,
			"blue": self.keyDisconnect,
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = session)
		self.createSetup()

	def createSetup(self):
		self.list = []
		self.hdmienabled = getConfigListEntry(_(_("HDMI CEC enabled:")), config.hdmicec.enabled)
		self.hdmidisabledtimerwakeup = getConfigListEntry(_(_("Disable power on actions for timer:")), config.hdmicec.disabletimerwakeup)
		self.hdmiactivesourcereply = getConfigListEntry(_(_("Active Source Reply On:")), config.hdmicec.active_source_reply)
		self.hdmitvstandby = getConfigListEntry(_("VU+ standby => TV activity:"), config.hdmicec.standby_message)
		self.hdmitvdeepstandby = getConfigListEntry(_("VU+ deepstandby => TV activity:"), config.hdmicec.deepstandby_message)
		self.hdmitvwakeupstandby = getConfigListEntry(_("VU+ on from standby => TV activity:"), config.hdmicec.wakeupstandby_message)
		self.hdmitvwakeupdeepstandby = getConfigListEntry(_("VU+ on from deepstandby => TV activity:"), config.hdmicec.wakeupdeepstandby_message)
		self.hdmivustandby = getConfigListEntry(_("TV standby => VU+ activity:"), config.hdmicec.vustandby_message)
		self.hdmivuwakeup = getConfigListEntry(_("TV on => VU+ activity:"), config.hdmicec.vuwakeup_message)
		self.hdmitvinput = getConfigListEntry(_("Choose TV HDMI input:"), config.hdmicec.tvinput)
		self.hdmiavinput = getConfigListEntry(_("Choose A/V-Receiver HDMI input:"), config.hdmicec.avinput)
		self.hdmiavvolumecontrol = getConfigListEntry(_("Use A/V-Receiver for volume control:"), config.hdmicec.avvolumecontrol)
		self.hdmiavvolup = getConfigListEntry(_("A/V-Receiver volume up:"), config.hdmicec.avvolup)
		self.hdmiavvoldown = getConfigListEntry(_("A/V-Receiver volume down:"), config.hdmicec.avvoldown)
		self.hdmiavvolmute = getConfigListEntry(_("A/V-Receiver toggle mute:"), config.hdmicec.avvolmute)
		self.hdmiavpwron = getConfigListEntry(_("A/V-Receiver power on:"), config.hdmicec.avpwron)
		self.hdmiavpwroff = getConfigListEntry(_("A/V-Receiver power off:"), config.hdmicec.avpwroff)
		self.hdmitvpwron = getConfigListEntry(_("TV power on:"), config.hdmicec.tvpwron)
		self.hdmitvpwroff = getConfigListEntry(_("TV power off:"), config.hdmicec.tvpwroff)
		self.hdmienabletvrc = getConfigListEntry(_("Use TV remotecontrol:"), config.hdmicec.enabletvrc)
		self.hdmidevicename = getConfigListEntry(_("Set VU+ device name:"), config.hdmicec.device_name)
		self.hdmiinputaddress = getConfigListEntry(_("Address (0~FF):"), config.hdmicec.input_address)
		self.hdmiinputvalue1 = getConfigListEntry("Value 1 (message):", config.hdmicec.input_value1)
		self.hdmiinputvalue2 = getConfigListEntry("Value 2 (optional):", config.hdmicec.input_value2)
		self.hdmiinputvalue3 = getConfigListEntry("Value 3 (optional):", config.hdmicec.input_value3)
		self.hdmiinputvalue4 = getConfigListEntry("Value 4 (optional):", config.hdmicec.input_value4)
		self.hdmilogenabledfile = getConfigListEntry(_("Enable debug output to file :"), config.hdmicec.logenabledfile)
		self.hdmilogenabledserial = getConfigListEntry(_("Enable debug output to console :"), config.hdmicec.logenabledserial)
		self.hdmimessagedelay = getConfigListEntry(_("Delay between CEC messages :"), config.hdmicec.message_delay)
# only used for testing
#		self.list.append( self.hdmiinputaddress )
#		self.list.append( self.hdmiinputvalue1 )
#		self.list.append( self.hdmiinputvalue2 )
#		self.list.append( self.hdmiinputvalue3 )
#		self.list.append( self.hdmiinputvalue4 )
#		self.list.append( self.hdmilogenabledfile )
# end testing
		self.list.append( self.hdmienabled )
		if config.hdmicec.enabled.value is True:
			self.list.append( self.hdmidevicename )
			self.list.append( self.hdmitvinput )
			self.list.append( self.hdmiavinput )
			self.list.append( self.hdmivuwakeup )
			self.list.append( self.hdmivustandby )
			self.list.append( self.hdmitvwakeupstandby )
			self.list.append( self.hdmitvwakeupdeepstandby )
			self.list.append( self.hdmitvstandby )
			self.list.append( self.hdmitvdeepstandby )
			self.list.append( self.hdmidisabledtimerwakeup )
			self.list.append( self.hdmienabletvrc )
			self.list.append( self.hdmimessagedelay )
			if config.hdmicec.avinput.value is not "0":
				self.list.append( self.hdmiavvolumecontrol )
				self.list.append( self.hdmiavvolup )
				self.list.append( self.hdmiavvoldown )
				self.list.append( self.hdmiavvolmute )
				self.list.append( self.hdmiavpwron )
				self.list.append( self.hdmiavpwroff )
			self.list.append( self.hdmitvpwron )
			self.list.append( self.hdmitvpwroff )
			self.list.append( self.hdmiactivesourcereply )
			self.list.append( self.hdmilogenabledserial )
			self.list.append( self.hdmilogenabledfile )
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyDisconnect(self):
		cmd = None
		logcmd = None
		physaddress1 = int("0x" + str(config.hdmicec.tvinput.value) + str(config.hdmicec.avinput.value),16)
		physaddress2 = int("0x00",16)
		address = int('0',16)
		cecmessage = int('0x9D',16)
		cecmessagetwo = physaddress1
		cecmessagethree = physaddress2
		cmd = struct.pack('BBB',cecmessage,cecmessagetwo,cecmessagethree)
		logcmd = lineno()+"send cec message %x:%x:%x to %x" % (cecmessage,cecmessagetwo,cecmessagethree,address)

		if cmd:
			eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))
			
		if logcmd:
			if config.hdmicec.logenabledserial.value:
				vtilog("[HDMICEC] "+logcmd)
				#if config.hdmicec.logenabledfile.value:
				#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
				#	system(filelog)
			if hdmi_cec.log:
				hdmi_cec.log.info(logcmd)

# only used for testing
	def keySend(self):
		cmd = None
		logcmd = None
		addresstmp=config.hdmicec.input_address.value
		tmp1=config.hdmicec.input_value1.value
		tmp2=config.hdmicec.input_value2.value
		tmp3=config.hdmicec.input_value3.value
		tmp4=config.hdmicec.input_value4.value
		address=int(addresstmp,16)
		if address not in range(0,256):
				address = 255
		if tmp4:
			val1=int(tmp1,16)
			val2=int(tmp2,16)
			val3=int(tmp3,16)
			val4=int(tmp4,16)
			if val1 not in range(0,256):
				val1 = 00
			if val2 not in range(0,256):
				val2 = 00
			if val3 not in range(0,256):
				val3 = 00
			if val4 not in range(0,256):
				val4 = 00
			cmd = struct.pack('BBBB',val1,val2,val3,val4)
			logcmd = lineno()+"** Test Message ** Send message value: %x:%x:%x:%x to address %x" % (val1,val2,val3,val4,address)
		else:

			if tmp3:
				val1=int(tmp1,16)
				val2=int(tmp2,16)
				val3=int(tmp3,16)
				if val1 not in range(0,256):
					val1 = 00
				if val2 not in range(0,256):
					val2 = 00
				if val3 not in range(0,256):
					val3 = 00
				cmd = struct.pack('BBB',val1,val2,val3)
				logcmd = lineno()+"** Test Message ** Send message value: %x:%x:%x to address %x" % (val1,val2,val3,address)
			else:

				if tmp2:
					val1=int(tmp1,16)
					val2=int(tmp2,16)
					if val1 not in range(0,256):
						val1 = 00
					if val2 not in range(0,256):
						val2 = 00
					cmd = struct.pack('BB',val1,val2)
					logcmd = lineno()+"** Test Message ** Send message value: %x:%x to address %x" % (val1,val2,address)
				else:
					val1=int(tmp1,16)
					if val1 not in range(0,256):
						val1 = 00
					cmd = struct.pack('B',val1)
					logcmd = lineno()+"** Test Message ** Send message value: %x to address %x" % (val1, address)

		if cmd:
			eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))
			
		if logcmd:
			if config.hdmicec.logenabledserial.value:
				vtilog("[HDMICEC] "+logcmd)
				#if config.hdmicec.logenabledfile.value:
				#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
				#	system(filelog)
			if hdmi_cec.log:
				hdmi_cec.log.info(logcmd)
# end testing

	def keyOk(self):
		cmd = None
		logcmd = None
		if self["config"].getCurrent() == self.hdmiavvolup:
			address = int("5",16)
			cecmessage = int("44",16)
			cecmessagetwo = int("41",16)
			cmd = struct.pack('BB',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)
		elif self["config"].getCurrent() == self.hdmiavvoldown:
			address = int("5",16)
			cecmessage = int("44",16)
			cecmessagetwo = int("42",16)
			cmd = struct.pack('BB',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)
		elif self["config"].getCurrent() == self.hdmiavvolmute:
			address = int("5",16)
			cecmessage = int("44",16)
			cecmessagetwo = int("43",16)
			cmd = struct.pack('BB',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)
		elif self["config"].getCurrent() == self.hdmiavpwron:
			address = int("5",16)
			cecmessage = int("44",16)
			cecmessagetwo = int("6D",16)
			cmd = struct.pack('BB',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)
		elif self["config"].getCurrent() == self.hdmiavpwroff:
			address = int("5",16)
			cecmessage = int("44",16)
			cecmessagetwo = int("6C",16)
			cmd = struct.pack('BB',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)
		elif self["config"].getCurrent() == self.hdmitvpwroff:
			address = int("0",16)
			cecmessage = int("36",16)
			cmd = struct.pack('B',cecmessage)
			logcmd = lineno()+"send cec message %x to %x" % (cecmessage,address)
		elif self["config"].getCurrent() == self.hdmitvpwron:
			address = int("0",16)
			cecmessage = int("04",16)
			cmd = struct.pack('B',cecmessage)
			logcmd = lineno()+"send cec message %x to %x" % (cecmessage,address)
		else:
			ConfigListScreen.keySave(self)
		if cmd:
			eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))

		if logcmd:
			if config.hdmicec.logenabledserial.value:
				vtilog("[HDMICEC] "+logcmd)
				#if config.hdmicec.logenabledfile.value:
				#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
				#	system(filelog)
			if hdmi_cec.log:
				hdmi_cec.log.info(logcmd)

	def keyConnect(self):
			hdmi_cec.activateSourceTimer()
			address = 0
			message = 0x85
			messageReceived(None, address, message)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent() == self.hdmienabled:
			self.createSetup()
		if self["config"].getCurrent() == self.hdmiavinput:
			self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent() == self.hdmienabled:
			self.createSetup()
		if self["config"].getCurrent() == self.hdmiavinput:
			self.createSetup()

	def keyCancel(self):
		self.close()

	def keySave(self):
		ConfigListScreen.keySave(self)

def openconfig(session, **kwargs):
	session.open(HdmiCecPlugin)

log = None

def autostart(reason, **kwargs):
	global session
	global log
	if kwargs.has_key("session") and reason == 0:
		if True: # config.hdmicec.enabled.value:
			if True: # config.hdmicec.logenabledfile.value:
				hdmi_cec.log = logging.getLogger("VTI HDMI-CEC")
				hdmi_cec.log.setLevel(logging.INFO)
				loghandler = logging.FileHandler("/tmp/hdmicec.log")
				loghandler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
				hdmi_cec.log.addHandler(loghandler)
				hdmi_cec.log.info(lineno()+"** PlugIn Start")
			session = kwargs["session"]
			if config.hdmicec.avvolumecontrol.value:
				## from InfoBarGenerics.py
				eActionMap.getInstance().bindAction('', -0x7FFFFFFF, volumekeyPressed)
				##
			eHdmiCEC.getInstance().cecMessageReceived.get().append(messageReceived)
			eHdmiCEC.getInstance().messageReceivedKey.get().append(messageReceivedKey)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("VTI HDMI-CEC"), description="VTI HDMI-CEC Configuration", where = PluginDescriptor.WHERE_PLUGINMENU, icon="hdmicec.png", needsRestart = True, fnc=openconfig),
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)]

def volumekeyPressed(key, flag):
	if config.hdmicec.avvolumecontrol.value and config.hdmicec.enabled.value and config.hdmicec.avinput.value != "0":
		if key == 113 or key == 114 or key == 115:
			address = int("5",16)
			cecmessagesendkey = int("44",16)
			cecmessagekeyevent = None
			if flag == 1:
				cecmessagekeybreak = int("45",16)
				cmd = struct.pack('B',cecmessagekeybreak)
			else:
				if key == 113:
					cecmessagekeyevent = int("43",16)
				elif key == 114:
					cecmessagekeyevent = int("42",16)
				elif key == 115:
					cecmessagekeyevent = int("41",16)
				if cecmessagekeyevent:
					cmd = struct.pack('BB',cecmessagesendkey,cecmessagekeyevent)
			if cmd:
				eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))
			return 1
	return 0

CecMsg = {
			0x00: "Feature Abort / Unsupported",
			0x04: "TV Image View On",
			0x0d: "TV Text View On",
			0x32: "Set Menu Language",
			0x36: "Standby",
			0x46: "Request Device Name",
			0x47: "Set Name",
			0x80: "Active HDMI from to : ",
			0x82: "Active Source  PhyAdr : ",
			0x83: "Request Physical Address",
			0x84: "Physical Address : ",
			0x85: "Request Active Source",
			0x87: "Vendor ID : ",
			0x8c: "Give Device Vendor ID",
			0x8d: "Request Menu State",
			0x8e: "Menu On",
			0x8f: "Request Power State",
			0x90: "Power State : ",
			0x91: "Get Menu Language",
			0x9d: "Inactive Source  PhyAdr : ",
			0x9e: "CEC Version : ",
			0x9f: "Request CEC Version",
			0xa0: "Vendor Command With ID",
			0xff: "Abort / Reserved"
}

def messageReceived(cecdata, manual_address = None, manual_cmd = None ):
	global log
	data = 16 * '\x00'
	length = 0
	if cecdata is not None:
		message = cecdata.getCommand()
		address = cecdata.getAddress()
		length = cecdata.getData(data, len(data))
	elif manual_address is not None and manual_cmd is not None:
		message = manual_cmd
		address = manual_address
	#logcmd = lineno()+"received cec message %x from %x" % (message, address)
	logcmd = lineno()+"%1x>%1x %02x (%s)" % (address&0xF, address>>4, message, CecMsg.get(message, "Unknown Message"))
	for ci in range(length):
		logcmd += " %02x" % ord(data[ci])
	if config.hdmicec.logenabledserial.value:
		vtilog("[HDMICEC] "+logcmd)
		#if config.hdmicec.logenabledfile.value:
		#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
		#	system(filelog)
	if hdmi_cec.log:
		hdmi_cec.log.info(logcmd)

	if config.hdmicec.enabled.value:
		from Screens.Standby import inStandby
		from Screens.Standby import Standby

		cmd = None
		cmdtwo = None
		addresstwo = None
		logcmd = None
		logcmdtwo = None

		physaddress1 = int("0x" + str(config.hdmicec.tvinput.value) + str(config.hdmicec.avinput.value),16)
		physaddress2 = int("0x00",16)

		addresstv = int("0x00",16)
		addressav = int("0x05",16)
		addressglobal = int("0x0F",16)

		cecversionreportmessage = int("0x9E",16)
		cecversionmessage = int("0x04",16)
		powerstatereportmessage = int("0x90",16)
		powerstateOff = int("0x01",16)
		powerstateOn = int("0x00",16)

		physaddressmessage = int('0x84',16)
		devicetypmessage = int('0x01',16)

		activesourcemessage = int('0x82',16)
		vendoridmessage = int('0x87',16)

		menuonmessage = int('0x8E',16)
		menustatemessage = int('0x00',16)

		setnamemessage = int('0x47',16)

		sendkeymessage = int("44",16)
		sendkeypwronmessage = int("6D",16)
		sendkeypwroffmessage = int("6C",16)

		if message == 0x8f: # request power state
			address = addresstv
			cecmessage = powerstatereportmessage
			cecmessagetwo = powerstateOn
			if (inStandby) and (config.hdmicec.vuwakeup_message.value == "vuwakeup"):
				cecmessagetwo = powerstateOff
			cmd = struct.pack('BB',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)

		if message == 0x9f: # request cec version
			address = addresstv
			cecmessage = cecversionreportmessage
			cecmessagetwo = cecversionmessage
			cmd = struct.pack('BB',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)

		elif message == 0x83: # request physical address
			if (inStandby) and (config.hdmicec.vuwakeup_message.value == "vuwakeup"):
				inStandby.Power()
			address = addressglobal
			cecmessage = physaddressmessage
			cecmessagetwo = physaddress1
			cecmessagethree = physaddress2
			cecmessagefour = devicetypmessage
			cmd = struct.pack('BBBB',cecmessage,cecmessagetwo,cecmessagethree,cecmessagefour)
			logcmd = lineno()+"send cec message %x:%x:%x:%x to %x" % (cecmessage,cecmessagetwo,cecmessagethree,cecmessagefour,address)

		elif message == 0x86:
			physicaladdress = ord(data[0]) * 256 + ord(data[1])
			pysaddrrstr = "%x" % (physicaladdress)
			confAddress = "%x%02x" % (physaddress1, physaddress2)
			if pysaddrrstr == confAddress:
				if (inStandby) and (config.hdmicec.vuwakeup_message.value == "vuwakeup"):
					inStandby.Power()
				address = addressglobal
				cecmessage = activesourcemessage
				cecmessagetwo = physaddress1
				cecmessagethree = physaddress2
				cmd = struct.pack('BBB',cecmessage,cecmessagetwo,cecmessagethree)
				logcmd = lineno()+"send cec message %x:%x:%x to %x" % (cecmessage,cecmessagetwo,cecmessagethree,address)
				eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))
				if config.hdmicec.enabletvrc.value:
					addresstwo = addresstv
					cecmessage = menuonmessage
					cecmessagetwo = menustatemessage
					cmdtwo = struct.pack('BB',cecmessage,cecmessagetwo)
					eHdmiCEC.getInstance().sendMessage(addresstwo, len(cmdtwo), str(cmdtwo))
			else:
				logcmd = lineno()+"received %x with data %x my conf %s" % (message,physicaladdress, confAddress)

		elif message == 0x8d: # request menu state
			if config.hdmicec.enabletvrc.value:
				address = addresstv
				cecmessage = menuonmessage
				cecmessagetwo = menustatemessage
				cmd = struct.pack('BB',cecmessage,cecmessagetwo)
				logcmd = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)

		elif message == 0x46: # request device name
			address = addresstv
			cecmessage = setnamemessage
			name_len = len(config.hdmicec.device_name.value)
			if name_len == 0:
				cecmessagetwo ="VU+"
				cmd = struct.pack('B4s',cecmessage,cecmessagetwo)
			else:
				cecmessagetwo = config.hdmicec.device_name.value
				cmd = struct.pack('B'+str(name_len+1)+'s',cecmessage,cecmessagetwo)
			logcmd = lineno()+"send cec message %x:%s to %x" % (cecmessage,cecmessagetwo,address)

		elif message == 0x85: # request active source
			if not inStandby:
				if config.hdmicec.active_source_reply.value or hdmi_cec.initial_active_source_call == True:
					address = addressglobal
					cecmessage = activesourcemessage
					cecmessagetwo = physaddress1
					cecmessagethree = physaddress2
					cmd = struct.pack('BBB',cecmessage,cecmessagetwo,cecmessagethree)
					logcmd = lineno()+"send cec message %x:%x:%x to %x" % (cecmessage,cecmessagetwo,cecmessagethree,address)
				if config.hdmicec.enabletvrc.value:
					addresstwo = addresstv
					cecmessage = menuonmessage
					cecmessagetwo = menustatemessage
					cmdtwo = struct.pack('BB',cecmessage,cecmessagetwo)
					logcmdtwo = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)
			elif inStandby:
				if config.hdmicec.vuwakeup_message.value == "vuwakeup":
					inStandby.Power()
					address = addressglobal
					cecmessage = activesourcemessage
					cecmessagetwo = physaddress1
					cecmessagethree = physaddress2
					cmd = struct.pack('BBB',cecmessage,cecmessagetwo,cecmessagethree)
					logcmd = lineno()+"send cec message %x:%x:%x to %x" % (cecmessage,cecmessagetwo,cecmessagethree,address)
					if config.hdmicec.enabletvrc.value:
						addresstwo = addresstv
						cecmessage = menuonmessage
						cecmessagetwo = menustatemessage
						cmdtwo = struct.pack('BB',cecmessage,cecmessagetwo)
						logcmdtwo = lineno()+"send cec message %x:%x to %x" % (cecmessage,cecmessagetwo,address)

		elif message == 0x36:
			if config.hdmicec.vustandby_message.value == "vustandby":
				if inStandby == None:
					logcmd = lineno()+"VU+ STB goto standby"
					session.open(Standby)
			elif config.hdmicec.vustandby_message.value == "vudeepstandby":
				import Screens.Standby
				logcmd = lineno()+"VU+ STB goto deepstandby"
				session.open(Screens.Standby.TryQuitMainloop,1)

		if inStandby == None:
			if cmd:
				eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))
			if cmdtwo:
				eHdmiCEC.getInstance().sendMessage(addresstwo, len(cmdtwo), str(cmdtwo))
			if logcmd:
				if config.hdmicec.logenabledserial.value:
					vtilog("[HDMICEC] "+logcmd)
					#if config.hdmicec.logenabledfile.value:
					#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
					#	system(filelog)
				if hdmi_cec.log:
					hdmi_cec.log.info(logcmd)
			if logcmdtwo:
				if config.hdmicec.logenabledserial.value:
					vtilog("[HDMICEC] "+logcmdtwo)
					#if config.hdmicec.logenabledfile.value:
					#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmdtwo)
					#	system(filelog)
				if hdmi_cec.log:
					hdmi_cec.log.info(logcmdtwo)

def messageReceivedKey(address, message):
	#logcmd = lineno()+"received cec message part two %x from %x" % (message, address)
	logcmd = lineno()+"RecvK %02x: %02x" % (address, message)
	if logcmd:
		if config.hdmicec.logenabledserial.value:
			vtilog("[HDMICEC] "+logcmd)
			#if config.hdmicec.logenabledfile.value:
			#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
			#	system(filelog)
		if hdmi_cec.log:
			hdmi_cec.log.info(logcmd)

	if config.hdmicec.enabled.value is True:
		rcdevicename = iInputDevices.getDeviceName('event0') # hschang : get rc device name, /dev/input/event0
		keyaction = eActionMap.getInstance()
		key = None
		if message == 0x32 or message == 0x09: #key menu
			key = int(139)
		elif message == 0x20: #key 0
			key = int(11)
		elif message == 0x21: #key 1
			key = int(2)
		elif message == 0x22: #key 2
			key = int(3)
		elif message == 0x23: #key 3
			key = int(4)
		elif message == 0x24: #key 4
			key = int(5)
		elif message == 0x25: #key 5
			key = int(6)
		elif message == 0x26: #key 6
			key = int(7)
		elif message == 0x27: #key 7
			key = int(8)
		elif message == 0x28: #key 8
			key = int(9)
		elif message == 0x29: #key 10
			key = int(10)
		elif message == 0x30: #key bouquet up
			key = int(402)
		elif message == 0x31: #key bouquet down
			key = int(403)
		elif message == 0x53: #key info/epg
			key = int(358)
		elif message == 0x00: #key ok
			key = int(352)
		elif message == 0x03: #key left
			key = int(105)
		elif message == 0x04: #key right
			key = int(106)
		elif message == 0x01: #key up
			key = int(103)
		elif message == 0x02: #key down
			key = int(108)
		elif message == 0x0d: #key exit
			key = int(174)
		elif message == 0x72: #key red
			key = int(398)
		elif message == 0x71: #key blue
			key = int(401)
		elif message == 0x73: #key green
			key = int(399)
		elif message == 0x74: #key yellow
			key = int(400)
		elif message == 0x44: #key play
			if rcdevicename.find("advanced"):
				key = int(164) # KEY_PLAYPAUSE
			else:
				key = int(207) # KEY_PLAY
		elif message == 0x46: #key pause
			if rcdevicename.find("advanced"):
				key = int(164) # KEY_PLAYPAUSE
			else:
				key = int(119) # KEY_PAUSE
		elif message == 0x45: #key stop
			key = int(128)
		elif message == 0x47: #key record
			key = int(167)
		elif message == 0x49: #fast forward
			if rcdevicename.find("advanced"):
				key = int(163) # KEY_NEXTSONG
			else:
				key = int(208) # KEY_FASTFORWARD
		elif message == 0x48: #rewind
			if rcdevicename.find("advanced"):
				key = int(165) # KEY_NEXTSONG
			else:
				key = int(168) # KEY_FASTFORWARD
		elif message == 0x60: #play 2
			key = int(207)
		elif message == 0x61: #key pause 2
			if rcdevicename.find("advanced"):
				key = int(164) # KEY_PLAYPAUSE
			else:
				key = int(119) # KEY_PAUSE
		elif message == 0x64: #key stop 2
			key = int(128)
		elif message == 0x62: #key record 2
			key = int(167)
#end translate keycodes
		if key:
			keyaction.keyPressed(rcdevicename, key, int(0))
			keyaction.keyPressed(rcdevicename, key, int(1))
