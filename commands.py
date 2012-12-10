from twisted.protocols import amp

class CommandOne(amp.Command):
	arguments = []
	response = [('offset', amp.Integer()), ('value', amp.Integer()), ('stop', amp.Boolean())]

class CommandTwo(amp.Command):
	arguments = [('arg1', amp.Integer()), ('arg2', amp.Integer())]
	response = [('outputTwo', amp.Integer())]

class CommandThree(amp.Command):
	arguments = [('arg1', amp.String())]
	response = []
