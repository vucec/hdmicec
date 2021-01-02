# -*- coding: utf-8 -*-

# maintainer: <info@vuplus-support.org>

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.

import struct
from enigma import eHdmiCEC, eTimer
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigSubsection, ConfigText
from Tools.HardwareInfo import HardwareInfo
from Screens.Standby import inStandby
import Screens.Standby
from Tools import Notifications
from Tools.DreamboxHardware import getFPWasTimerWakeup
from Tools.Directories import fileExists
import time
from os import system

import inspect

def loghdr():
    """Returns log header with current line number in HdmiCec.py."""
    return "[VTI HDMI-CEC] H%03d  " % inspect.currentframe().f_back.f_lineno

class HdmiCec:
	def __init__(self):
		config.hdmicec = ConfigSubsection()
		config.hdmicec.enabled = ConfigYesNo(default = False)
		config.hdmicec.logenabledserial = ConfigYesNo(default = False)
		config.hdmicec.logenabledfile = ConfigYesNo(default = False)
		config.hdmicec.tvstandby = ConfigYesNo(default = False)
		config.hdmicec.tvwakeup = ConfigYesNo(default = False)
		config.hdmicec.boxstandby = ConfigYesNo(default = False)
		config.hdmicec.enabletvrc = ConfigYesNo(default = True)
		config.hdmicec.active_source_reply = ConfigYesNo(default = True)
		config.hdmicec.avvolumecontrol = ConfigYesNo(default = False)
		config.hdmicec.disabletimerwakeup = ConfigYesNo(default = True)
		config.hdmicec.device_name = ConfigText(default = self.getDeviceName(), visible_width = 50, fixed_size = False)
		config.hdmicec.standby_message = ConfigSelection(default = "standby,inactive", 
			choices = [
			("standby,inactive", _("TV standby")),
			("standby,avpwroff,inactive,", _("TV + A/V standby")),
			("inactive", _("Source inactive")),
			("nothing", _("Nothing"))])
		config.hdmicec.deepstandby_message = ConfigSelection(default = "standby,inactive",
			choices = [
			("standby,inactive", _("TV standby")),
			("standby,avdeeppwroff,inactive", _("TV + A/V standby")),
			("inactive", _("Source inactive")),
			("nothing", _("Nothing"))])
		config.hdmicec.wakeupstandby_message = ConfigSelection(default = "wakeup,active,activevu",
			choices = [
			("wakeup,active,activevu", _("TV wakeup")),
			("wakeup,active,activevu,avpwron", _("TV + A/V wakeup")),
			("avpwron,wakeup,active,activevu", _("A/V + TV wakeup")),
			("active", _("Source active")),
			("nothing", _("Nothing"))])
		config.hdmicec.wakeupdeepstandby_message = ConfigSelection(default = "wakeup,active,activevu",
			choices = [
			("wakeup,active,activevu", _("TV wakeup")),
			("wakeup,active,activevu,avpwron", _("TV + A/V wakeup")),
			("avpwron,wakeup,active,activevu", _("A/V + TV wakeup")),
			("active", _("Source active")),
			("nothing", _("Nothing"))])
		config.hdmicec.vustandby_message = ConfigSelection(default = "vustandby",
			choices = [
			("vustandby", _("VU+ standby")),
			("vudeepstandby", _("VU+ DeepStandby")),
			("vunothing", _("Nothing"))])
		config.hdmicec.vuwakeup_message = ConfigSelection(default = "vuwakeup",
			choices = [
			("vuwakeup", _("VU+ wakeup")),
			("vunothing", _("Nothing"))])
		config.hdmicec.tvinput = ConfigSelection(default = "1",
			choices = [
			("1", "HDMI 1"),
			("2", "HDMI 2"),
			("3", "HDMI 3"),
			("4", "HDMI 4"),
			("5", "HDMI 5"),
			("6", "HDMI 6"),
			("7", "HDMI 7")])
		config.hdmicec.avinput = ConfigSelection(default ="0",
			choices = [
			("0", _("no A/V Receiver")),
			("1", "HDMI 1"),
			("2", "HDMI 2"),
			("3", "HDMI 3"),
			("4", "HDMI 4"),
			("5", "HDMI 5"),
			("6", "HDMI 6"),
			("7", "HDMI 7")])
		config.hdmicec.message_delay = ConfigSelection(default = "10",
			choices = [
			("1", "0.1 sec"),
			("5", "0.5 sec"),
			("10", "1 sec"),
			("20", "2 sec"),
			("30", "3 sec"),
			("50", "5 sec")])

		self.cecmessage_queue = []
		self.delayTimer = eTimer()
		self.delayTimer.callback.append(self.sendCECMessage)
		self.delayTimer_intervall = int(config.hdmicec.message_delay.value) * 100
		config.misc.standbyCounter.addNotifier(self.enterStandby, initial_call = False)
		config.misc.DeepStandbyOn.addNotifier(self.enterDeepStandby, initial_call = False)
		self.activateSourceTimer()
		self.leaveDeepStandby()

	def getDeviceName(self):
		return "Vu+ " + HardwareInfo().get_friendly_name()

	def sendMessages(self, messages, delay = True):
		messagedelay = float(config.hdmicec.message_delay.value)/10.0
		for message in messages.split(','):
			cmd = None
			logcmd = None
			addressvaluebroadcast = int("0F",16)
			addressvalue = int("0",16)
			addressvalueav = int("5",16)
			wakeupmessage = int("04",16)
			standbymessage=int("36",16)
			activesourcemessage=int("82",16)
			inactivesourcemessage=int("9D",16)
			sendkeymessage = int("44",16)
			sendkeypwronmessage = int("6D",16)
			sendkeypwroffmessage = int("6C",16)
			activevumessage=int("85",16)
			physaddressmessage = int('0x84',16)
			devicetypmessage = int('0x01',16)
			physaddress1 = int("0x" + str(config.hdmicec.tvinput.value) + str(config.hdmicec.avinput.value),16)
			physaddress2 = int("0x00",16)
			setnamemessage = int('0x47',16)
			if message == "wakeup":
				cmd = struct.pack('B', wakeupmessage)
				logcmd = loghdr()+"** WakeUpMessage ** send message: %x to address %x" % (wakeupmessage, addressvalue)
			elif message == "active":
				addressvalue = addressvaluebroadcast
				cmd = struct.pack('BBB', activesourcemessage,physaddress1,physaddress2)
				logcmd = loghdr()+"** ActiveSourceMessage ** send message: %x:%x:%x to address %x" % (activesourcemessage,physaddress1,physaddress2,addressvalue)
				self.delayed_Message_Timer = eTimer()
				self.delayed_Message_Timer.start(20000, True)
				self.delayed_Message_Timer.callback.append(self.delayedActiveSourceMessage)
			elif message == "standby":
				cmd = struct.pack('B', standbymessage)
				logcmd = loghdr()+"** StandByMessage ** send message: %x to address %x" % (standbymessage, addressvalue)
			elif message == "inactive":
				addressvalue = addressvaluebroadcast
				cmd = struct.pack('BBB', inactivesourcemessage,physaddress1,physaddress2)
				logcmd = loghdr()+"** InActiveSourceMessage ** send message: %x:%x:%x to address %x" % (inactivesourcemessage,physaddress1,physaddress2,addressvalue)
			elif message == "avpwron":
				cmd = struct.pack('BB', sendkeymessage,sendkeypwronmessage)
				addressvalue = addressvalueav
				logcmd = loghdr()+"** Power on A/V ** send message: %x:%x to address %x" % (sendkeymessage, sendkeypwronmessage, addressvalue)
			elif message == "avdeeppwroff":
				cmd = struct.pack('BB',sendkeymessage,sendkeypwroffmessage)
				addressvalue = addressvalueav
				logcmd = loghdr()+"** Standby A/V (Deepstandby)** send message: %x:%x to address %x" % (sendkeymessage,sendkeypwroffmessage, addressvalue)
			elif message == "avpwroff":
				addressvalue = addressvalueav
				cmd = struct.pack('BB',sendkeymessage,sendkeypwroffmessage)
				logcmd = loghdr()+"** Standby A/V ** send message: %x:%x to address %x" % (sendkeymessage,sendkeypwroffmessage, addressvalue)
			elif message == "activevu":
				addressvalue = addressvaluebroadcast
				cmd = struct.pack('B', activevumessage)
				logcmd = loghdr()+"** Active VU Message ** send message: %x to address %x" % (activevumessage,addressvalue)
			elif message == "physaddress":
				addressvalue = addressvaluebroadcast
				cmd = struct.pack('BBBB',physaddressmessage,physaddress1,physaddress2,devicetypmessage)
				logcmd = loghdr()+"** Report phys address %x:%x:%x:%x to %x" % (physaddressmessage,physaddress1,physaddress2,devicetypmessage,addressvalue)
			elif message == "setdevicename":
				cecmessage = setnamemessage
				name_len = len(config.hdmicec.device_name.value)
				if name_len == 0:
					cecmessagetwo ="VU+"
					cmd = struct.pack('B4s',cecmessage,cecmessagetwo)
				else:
					cecmessagetwo = config.hdmicec.device_name.value
					cmd = struct.pack('B'+str(name_len+1)+'s',cecmessage,cecmessagetwo)
				logcmd = loghdr()+"** Send device name  %x:%s to %x" % (cecmessage,cecmessagetwo,addressvalue)
			if cmd and logcmd:
				self.cecmessage_queue.append((cmd, addressvalue, logcmd))
		if not delay:
			self.sendCECMessage(delay = False)
		else:
			self.delayTimer.start(self.delayTimer_intervall, True)

	def sendCECMessage(self, delay = True):
		self.delayTimer.stop()
		if len(self.cecmessage_queue):
			cmd, addressvalue, logcmd = self.cecmessage_queue.pop(0)
			eHdmiCEC.getInstance().sendMessage(addressvalue, len(cmd), str(cmd))
			if config.hdmicec.logenabledserial.value:
				vtilog(logcmd)
				#if config.hdmicec.logenabledfile.value:
				#	filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
				#	system(filelog)
			if self.log:
				self.log.info(logcmd)
			if len(self.cecmessage_queue):
				if not delay:
					messagedelay = float(config.hdmicec.message_delay.value)/10.0
					time.sleep(messagedelay)
					self.sendCECMessage(delay = False)
				else:
					self.delayTimer.start(self.delayTimer_intervall, True)

	def delayedActiveSourceMessage(self):
		messagedelay = float(config.hdmicec.message_delay.value)/10.0
		addressvaluebroadcast = int("0F",16)
		activesourcemessage=int("82",16)
		activevumessage=int("85",16)
		addressvalue = int("0",16)
		physaddress1 = int("0x" + str(config.hdmicec.tvinput.value) + str(config.hdmicec.avinput.value),16)
		physaddress2 = int("0x00",16)
		setnamemessage = int('0x47',16)
		addressvalue = addressvaluebroadcast
		physaddressmessage = int('0x84',16)
		devicetypmessage = int('0x01',16)
		from Screens.Standby import inStandby
		if not inStandby:
			cmd_active = struct.pack('BBB', activesourcemessage,physaddress1,physaddress2)
			logcmd_active = loghdr()+"** ActiveSourceMessage ** send message: %x:%x:%x to address %x" % (activesourcemessage,physaddress1,physaddress2,addressvalue)
			self.cecmessage_queue.append((cmd_active, addressvalue, logcmd_active))
			cmd_vu_is_active = struct.pack('B', activevumessage)
			logcmd_vu_is_active = loghdr()+"** Active VU Message ** send message: %x to address %x" % (activevumessage,addressvalue)
			self.cecmessage_queue.append((cmd_vu_is_active, addressvalue, logcmd_vu_is_active))
			cmd = struct.pack('BBBB',physaddressmessage,physaddress1,physaddress2,devicetypmessage)
			logcmd = loghdr()+"** Report phys address %x:%x:%x:%x to %x" % (physaddressmessage,physaddress1,physaddress2,devicetypmessage,addressvaluebroadcast)
			self.cecmessage_queue.append((cmd, addressvaluebroadcast, logcmd))
			name_len = len(config.hdmicec.device_name.value)
			if name_len > 0:
					cecmessagetwo = config.hdmicec.device_name.value
					cmd = struct.pack('B'+str(name_len+1)+'s',setnamemessage,config.hdmicec.device_name.value)
					logcmd = loghdr()+"** Send device name  %x:%s to %x" % (setnamemessage,config.hdmicec.device_name.value,addressvalue)
					self.cecmessage_queue.append((cmd, addressvalue, logcmd))
			if not self.delayTimer.isActive():
				self.delayTimer.start(self.delayTimer_intervall, True)

	def leaveStandby(self):
		if config.hdmicec.enabled.value:
			self.activateSourceTimer()
			msg = str(config.hdmicec.wakeupstandby_message.value)
			if not msg.find('nothing') != -1:
				msg += ",physaddress,setdevicename"
			self.sendMessages(config.hdmicec.wakeupstandby_message.value)

	def enterStandby(self, configElement):
		if hasattr(self, "activeSourceTimer"):
			self.activeSourceTimer.stop()
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.leaveStandby)
		if config.hdmicec.enabled.value:
			self.sendMessages(config.hdmicec.standby_message.value)
		if inStandby != None:
			self.sendMessages("inactive")

	def enterDeepStandby(self,configElement):
		if config.hdmicec.enabled.value:
			self.sendMessages(config.hdmicec.deepstandby_message.value, delay = False)

	def leaveDeepStandby(self):
		if config.hdmicec.enabled.value:
			msg = str(config.hdmicec.wakeupdeepstandby_message.value)
			if not msg.find('nothing') != -1:
				msg += ",physaddress,setdevicename"
			if not getFPWasTimerWakeup():
				self.sendMessages(msg)
			else:
				if config.hdmicec.disabletimerwakeup.value:
					vtilog(loghdr()+"timer wakeup => do not power on TV / A/V receiver")
					if self.log:
						self.log.info(loghdr()+"timer wakeup => do not power on TV / A/V receiver")
				else:
					self.sendMessages(msg)

	def activateSourceTimer(self):
		self.initial_active_source_call = True
		self.activeSourceTimer = eTimer()
		self.activeSourceTimer.callback.append(self.setActiveSourceCall)
		if config.hdmicec.active_source_reply.value == False:
			self.activeSourceTimer.start(60000, True)

	def setActiveSourceCall(self):
		self.initial_active_source_call = False
