#! /usr/bin/env python
# -*- coding: ascii -*-

# Sintassi ispirata a construct (htp://construct.wikispaces.com/)

# Copyright (c) 2009, Franco Bugnano
# All rights reserved.
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
#     1. The origin of this software must not be misrepresented; you must not
#     claim that you wrote the original software. If you use this software
#     in a product, an acknowledgment in the product documentation would be
#     appreciated but is not required.
#
#     2. Altered source versions must be plainly marked as such, and must not be
#     misrepresented as being the original software.
#
#     3. This notice may not be removed or altered from any source
#     distribution.

from __future__ import division

__version__ = '1.0.2'
__date__ = '2010-02-26'
__copyright__ = 'Copyright (C) 2009-2010, Franco Bugnano'

import struct
import copy

LITTLE_ENDIAN = '<'
BIG_ENDIAN = '>'

# Classe che mi serve per contenere i dati delle strutture
class StructData(object):
	def GetDict(self):
		d = {}
		for k, v in self.__dict__.iteritems():
			# Nel dizionario non includo questa funzione
			if k in ('GetDict', ):
				continue

			e = getattr(self, k)
			if hasattr(e, 'GetList'):
				d[k] = e.GetList()
			elif hasattr(e, 'GetDict'):
				d[k] = e.GetDict()
			else:
				d[k] = v

		return d


class ArrayData(list):
	def GetList(self):
		l = []
		for e in self:
			if hasattr(e, 'GetList'):
				l.append(e.GetList())
			elif hasattr(e, 'GetDict'):
				l.append(e.GetDict())
			else:
				l.append(e)

		return l


def StructDataFromDict(dct, encoding='cp1252'):
	struttura_dati = StructData()
	for k, v in dct.iteritems():
		if hasattr(v, 'iteritems'):
			setattr(struttura_dati, k, StructDataFromDict(v, encoding))
		elif hasattr(v, '__iter__'):
			setattr(struttura_dati, k, ArrayDataFromList(v, encoding))
		elif hasattr(v, 'encode'):
			setattr(struttura_dati, k, v.encode(encoding))
		else:
			setattr(struttura_dati, k, v)

	return struttura_dati


def ArrayDataFromList(lst, encoding='cp1252'):
	lista_dati = ArrayData()
	for e in lst:
		if hasattr(e, 'iteritems'):
			lista_dati.append(StructDataFromDict(e, encoding))
		elif hasattr(e, '__iter__'):
			lista_dati.append(ArrayDataFromList(e, encoding))
		elif hasattr(e, 'encode'):
			lista_dati.append(e.encode(encoding))
		else:
			lista_dati.append(e)

	return lista_dati


class BasicType(object):
	def __init__(self, nome, tipo):
		self.nome = nome
		self.tipo = tipo

		self.SetOffset(0)
		self.SetEndianess(BIG_ENDIAN)


	def GetSize(self):
		return struct.calcsize(''.join([self.endianess, self.tipo]))


	def GetOffset(self):
		return self.offset


	def SetOffset(self, offset):
		self.offset = offset


	def GetEndianess(self):
		return self.endianess


	def SetEndianess(self, endianess):
		self.endianess = endianess


	def Encode(self, data_):
		return struct.pack(''.join([self.endianess, self.tipo]), data_)


	def Decode(self, data_):
		return struct.unpack(''.join([self.endianess, self.tipo]), data_)[0]


	def __call__(self, nome):
		# Chiamare l'oggetto significa creare una nuova istanza con un nome diverso
		tmpobj = copy.deepcopy(self)
		tmpobj.nome = nome

		return tmpobj


# Tipi semplici
SInt8 = BasicType('SInt8', 'b')
UInt8 = BasicType('UInt8', 'B')
SInt16 = BasicType('SInt16', 'h')
UInt16 = BasicType('UInt16', 'H')
SInt32 = BasicType('SInt32', 'i')
UInt32 = BasicType('UInt32', 'I')
Float = BasicType('Float', 'f')
Double = BasicType('Double', 'd')


# La stringa e' un tipo particolare perche' richiede le dimensioni
class String(BasicType):
	def __init__(self, nome, dimensioni):
		tipo = '%us' % dimensioni

		super(String, self).__init__(nome, tipo)


# Tipi composti
class Array(BasicType):
	def __init__(self, nome, tipo_dati, num):
		# Step 1: Creo gli oggetti
		self.lista_oggetti = []
		for i in range(num):
			self.lista_oggetti.append(tipo_dati(''.join([nome, '[', str(i), ']'])))

		# Step 2: Calcolo dimensioni e offset
		if num > 0:
			tipo = self.lista_oggetti[0].tipo * num
			self.base_size = self.lista_oggetti[0].GetSize()
		else:
			tipo = ''
			self.base_size = 0

		super(Array, self).__init__(nome, tipo)


	def SetOffset(self, offset):
		# Step 1: Aggiorno il mio offset
		super(Array, self).SetOffset(offset)

		# Step 2: Aggiorno l'offset a tutti i miei elementi
		for i, e in enumerate(self.lista_oggetti):
			e.SetOffset(self.offset + (i * self.base_size))


	def SetEndianess(self, endianess):
		# Step 1: Aggiorno la mia endianess
		super(Array, self).SetEndianess(endianess)

		# Step 2: Aggiorno l'endianess a tutti i miei elementi
		for e in self.lista_oggetti:
			e.SetEndianess(endianess)


	def Encode(self, data_):
		# Dal momento che data_ puo' essere una lista non solo di tipi semplici, ma
		# anche una lista di classi, delego la codifica ad ogni singolo membro
		lista_stringhe = []
		for i, e in enumerate(self.lista_oggetti):
			lista_stringhe.append(e.Encode(data_[i]))

		return ''.join(lista_stringhe)


	def Decode(self, data_):
		# Dal momento che lista_dati puo' essere una lista non solo di tipi semplici, ma
		# anche una lista di classi, delego la decodifica ad ogni singolo membro
		lista_dati = ArrayData()
		data_offset = 0
		for e in self.lista_oggetti:
			lista_dati.append(e.Decode(data_[data_offset:data_offset + self.base_size]))
			data_offset += self.base_size

		return lista_dati


	def __getitem__(self, k):
		return self.lista_oggetti[k]


	def __len__(self):
		return len(self.lista_oggetti)


	def __iter__(self):
		return iter(self.lista_oggetti)


class Struct(BasicType):
	def __init__(self, nome, *args):
		# Step 1: Creo gli oggetti
		self.lista_oggetti = []
		for e in args:
			# Mi creo una copia locale di ogni elemento
			e_copia = e(e.nome)

			# Aggiorno il mio __dict__ per poter accedere ai membri per nome
			self.__dict__[e.nome] = e_copia

			self.lista_oggetti.append(e_copia)

		# Step 2: Calcolo dimensioni e offset
		tipo = ''.join([x.tipo for x in self.lista_oggetti])

		super(Struct, self).__init__(nome, tipo)


	def SetOffset(self, offset):
		# Step 1: Aggiorno il mio offset
		super(Struct, self).SetOffset(offset)

		# Step 2: Aggiorno l'offset a tutti i miei elementi
		accumulatore_offset = 0
		for e in self.lista_oggetti:
			e.SetOffset(self.offset + accumulatore_offset)
			accumulatore_offset += e.GetSize()


	def SetEndianess(self, endianess):
		# Step 1: Aggiorno la mia endianess
		super(Struct, self).SetEndianess(endianess)

		# Step 2: Aggiorno l'endianess a tutti i miei elementi
		for e in self.lista_oggetti:
			e.SetEndianess(endianess)


	def Encode(self, data_):
		# Delego la codifica ad ogni singolo membro nell'ordine
		lista_stringhe = []
		for e in self.lista_oggetti:
			lista_stringhe.append(e.Encode(getattr(data_, e.nome)))

		return ''.join(lista_stringhe)


	def Decode(self, data_):
		# Delego la decodifica ad ogni singolo membro nell'ordine
		struttura_dati = StructData()
		data_offset = 0
		for e in self.lista_oggetti:
			sz = e.GetSize()
			setattr(struttura_dati, e.nome, e.Decode(data_[data_offset:data_offset + sz]))
			data_offset += sz

		return struttura_dati

