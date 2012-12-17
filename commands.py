from twisted.protocols import amp
from BigStringVoodoo import *

class GetNextMutation(amp.Command):
    arguments = []
    response = [('offset', amp.Integer()), ('mutation_index', amp.Integer()), ('stop', amp.Boolean()), ('pause', amp.Boolean())]

class LogResults(amp.Command):
    arguments = [('mutation_index',amp.Integer()), ('offset',amp.Integer()), ('output',amp.String()), ('filename',amp.String())]
    response = []

class GetOriginalFile(amp.Command):
    arguments = []
    response = [('original_file_name', amp.String()), ('original_file', BigString())]

class GetProgram(amp.Command):
    arguments = []
    response = [('program', amp.String())]

class GetMutationTypes(amp.Command):
    arguments = []
    response = [('mutation_types', amp.AmpList([ ('value',amp.String()), ('type',amp.String()), ('size',amp.Integer()) ]))]

