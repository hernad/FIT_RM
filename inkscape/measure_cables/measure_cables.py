#!/usr/bin/env python 
'''
Copyright (C) 2010 Ernad Husremovic, hernad@bring.out.ba

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

-----------------------

This script finds all fonts in the current drawing that match the 
specified find font, and replaces them with the specified replacement
font.

It can also replace all fonts indiscriminately, and list all fonts
currently being used.
'''

import os
import sys
import inkex
import simplestyle
import cubicsuperpath, measure

desc_tag = '{http://www.w3.org/2000/svg}desc'

ns_path = inkex.addNS('path','svg')

def get_style(node):
	'''
	Sugar coated way to get style dict from a node
	'''
	if 'style' in node.attrib:
		return simplestyle.parseStyle(node.attrib['style'])

def set_style(node, style):
	'''
	Sugar coated way to set the style dict, for node
	'''
	node.attrib['style'] = simplestyle.formatStyle(style)

def die(msg = "Dying!"):
	inkex.errormsg(msg)
	sys.exit(0)


def is_path(node):
        return node.tag == ns_path

def report_replacements(num):
	'''
	Sends a message to the end user showing success of failure
	of the font replacement
	'''
	if num == 0:
		die('Couldn\'t find anything using that font, please ensure the spelling and spacing is correct.')

def report_findings(findings):
	'''
	Tells the user which fonts were found, if any
	'''
	if len(findings) == 0:
		inkex.errormsg("Didn't find any paths in this document/selection.")
	else:
		inkex.errormsg("Found the following paths:\n%s" % '\n'.join(findings))

class MeasureCables(inkex.Effect):
	'''
	Measure cables length, number of it etc
	'''
	def __init__(self):
		inkex.Effect.__init__(self)	
		self.OptionParser.add_option("--fr_find", action="store", 
										type="string", dest="fr_find",
										default=None, help="")
										
		self.OptionParser.add_option("--fr_replace", action="store", 
										type="string", dest="fr_replace", 
										default=None, help="")

		self.OptionParser.add_option("--r_replace", action="store", 
										type="string", dest="r_replace", 
										default=None, help="")

		self.OptionParser.add_option("--action", action="store", 
										type="string", dest="action", 
										default=None, help="")

		self.OptionParser.add_option("--scope", action="store", 
										type="string", dest="scope", 
										default=None, help="")

                # from measure.py
                self.OptionParser.add_option("-u", "--unit", 
                        action="store", type="string",  
                        dest="unit", default="mm", 
                        help="The unit of the measurement") 
                self.OptionParser.add_option("-p", "--precision", 
                        action="store", type="int",  
                        dest="precision", default=2, 
                        help="Number of significant digits after decimal point") 
                self.OptionParser.add_option("-s", "--scale", 
                        action="store", type="float",  
                        dest="scale", default=1, 
                        help="The distance above the curve")


        def factor(self):
               factor = None     
               if self.options.unit=="mm":
                    factor=25.4/90.0        # px->mm
               elif self.options.unit=="pt":
                    factor=0.80             # px->pt
               elif self.options.unit=="cm":
                    factor=25.4/900.0       # px->cm
               elif self.options.unit=="m":
                    factor=25.4/90000.0     # px->m
               elif self.options.unit=="km":
                    factor=25.4/90000000.0  # px->km
               elif self.options.unit=="in":
                    factor=1.0/90.0         # px->in
               elif self.options.unit=="ft":
                    factor=1.0/90.0/12.0    # px->ft
               elif self.options.unit=="yd":
                    factor=1.0/90.0/36.0    # px->yd
               else :
                    ''' Default unit is px'''
                    factor=1
                    self.options.unit="px"

               return factor


	def find_desc(self, node):
		'''
		Recursive method for appending all text-type elements
		to self.selected_items
		'''
                for subnode in node:
                   if subnode.tag == desc_tag:
                      return subnode.text
                else:
                   return None
                      
	def relevant_items(self, scope):
		'''
		Depending on the scope, returns all path elements, or all 
		selected text elements including nested children
		'''
		items = []
		to_return = []
		if scope == "layer":

			for item in self.current_layer.getiterator():
                             items.append(item)
			if len(items) == 0:
				die("There was nothing in layer")

		elif scope == "selection_only":
			items = []
			
                        for item in self.selected.iteritems():
                             items.append(item[1])
			if len(items) == 0:
				die("There was nothing selected")
		else:
			items = self.document.getroot().getiterator()
		to_return.extend(filter(is_path, items))
		return to_return

	def find_replace(self, nodes, find, replace):
		'''
		Walks through nodes, replacing fonts as it goes according
		to find and replace
		'''
		replacements = 0
		for node in nodes:
			if find_replace_font(node, find, replace):
				replacements += 1
		report_replacements(replacements)

	def replace_all(self, nodes, replace):
		'''
		Walks through nodes, setting fonts indiscriminately.
		'''
		replacements = 0
		for node in nodes:
			if set_font(node, replace):
				replacements += 1
		report_replacements(replacements)


       

	def list_all(self, nodes):
		'''
		Walks through nodes, building a list of all cables found, then 
		reports to the user with that list
		'''

                rpt = []

                cables = {}
                cnt = 0
                for node in nodes:
                   if is_path(node):
		       style = get_style(node)
                       p = cubicsuperpath.parsePath(node.get('d'))
                       slengths, stotal = measure.csplength(p)
                       cable_length =  ('{0:.'+str(self.options.precision)+'f}').format(stotal*self.factor()*self.options.scale)
                       description = self.find_desc(node)
                       try:   
                          rpt.append("path %s x %d" % (cable_length, int(description)))
                          if cable_length in cables.keys():
                             cables[cable_length] += int(description)
                          else:
                             cables[cable_length] = int(description)
                       except:
                          style['stroke'] = "#ff0000"
                          style['stroke-width'] = "10px"
                          #style['marker-start'] = "url(#DotL)"
                          set_style(node, style)
                       cnt += 1

                       keys = cables.keys()
                       keys.sort()
                       sorted_cables = map(cables.get, keys)

                       items = cables.items()
                       items.sort( key=lambda int(cables):cables[0])
                       rpt.append("%s" % (cables))
                       rpt.append("%s" % (items))
                rpt.append("Broj path-ova = %s" % (cnt))
   
		report_findings(rpt)

	def effect(self):
		action = self.options.action.strip("\"") # TODO Report this bug (Extra " characters)
		scope = self.options.scope

		relevant_items = self.relevant_items(scope)

		if action == "find_replace":
			find = self.options.fr_find.strip().lower()
			replace = self.options.fr_replace
			self.find_replace(relevant_items, find, replace)
		elif action == "replace_all":
			replace = self.options.r_replace
			self.replace_all(relevant_items, replace)
		elif action == "list_only":
			self.list_all(relevant_items)
			#sys.exit(0)

if __name__ == "__main__":
	e = MeasureCables()
	e.affect()

