#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version Mon 6 April 2020

@author: Sebastian Mueller
"""

from os import remove   
from sys import argv 
from subprocess import Popen
from shutil import which
from argparse import ArgumentParser
from PIL import Image 
from pdfrw import PdfReader, PdfWriter, PageMerge

#Missing libraries have to be installed using pip, conda or similar. 
#An installation of pdfrw from conda is possible using conda-forge https://github.com/conda-forge/pdfrw-feedstock.
#In addition Ghostscript has to be installed.
#Windows/Linux: https://www.ghostscript.com/download/gsdnld.html 
#Mac: http://macappstore.org/ghostscript

class Ghostscript:
    
    def __init__(self): 
        names = ['gs', 'gswin32c', 'gswin64c', '/usr/local/bin/gs', '/usr/bin/gs']
        i = 0
        while (i<=len(names)-1) and (which(names[i]) is None):
            i += 1
        if i <= len(names)-1:
            self.command = names[i]
        else:
            raise Exception("Install Ghostscript.") 
            
    def pdf2jpg(self, filename):
        process = Popen([self.command,'-dBATCH', '-dNOPAUSE', '-sOutputFile=%s.jpg' % filename, '-r200', '-sDEVICE=jpeg', '-q', filename+'.pdf'])
        process.wait()
    
    def flatten_pdf(self, infile, outfile): 
        process = Popen([self.command, '-dBATCH', '-dNOPAUSE', '-sOutputFile=%s.pdf' % outfile, '-dPreserveAnnots=false', '-r200','-sDEVICE=pdfwrite', '-q', infile + '.pdf'])
        process.wait()
        
sides = 5
color_tol = 120

def pixel_is_white(pixel): 
    if type(pixel) == int: 
        return pixel>=255-color_tol
    else:
        for i in range(3):
            if pixel[i]<255-color_tol:
                return False
        return True  

def line_is_white(w,h,pixels,line):
    for column in range(sides,w-sides): 
        pixel = pixels[column,line]
        if not pixel_is_white(pixel):
            return False 
    return True    

def move_until_white(w,h,pixels,start,white):
    line = start
    while line_is_white(w,h,pixels,line)!=white and line<h-sides: 
        line = line+1    
    return line 
    
def endpoints(w,h,pixels): 
    result = [sides]
    line = sides
    line = move_until_white(w,h,pixels,line,False) # go to start of first writing
    while (line<h-sides):
        line = move_until_white(w,h,pixels,line,True) # go to start of gap
        if line<h-sides:
            line = move_until_white(w,h,pixels,line,False) 
        result.append(line-1)
    return result
                 
"""
The most important optional arguments are also available as command line options
and explained in slide_name_command_line()

Additional options:
two_screens: by default, for placement=left we still start writing on the left in the beginning of the document (similar for placement=top), 
  this may be undesired if the slides are supposed to appear on separate screens, it is deactivated by setting two_screens=True  
skip_pages: skip a number of slides in the end
"""
    
def make_slides(name, rotate=0, history=True, anim=True, place='left', add_name='_slides', two_screens=False, skip_pages=0):
    
    # create white image
    Image.new('RGB', (1, 1), (255, 255, 255)).save('white.pdf')
    white = PdfReader('white.pdf').pages[0] 
    # integrate annotations and read file 
    gs = Ghostscript()
    gs.flatten_pdf(name, name + '_flat')
    pdf = PdfReader(name + '_flat.pdf')
    out = PdfWriter()  
    for j in range(len(pdf.pages)-skip_pages):
        print('slide', j+1)
        pdf.pages[j].Rotate = rotate
        # get pixels
        temp_out = PdfWriter()
        temp_out.addpage(pdf.pages[j])
        temp_out.write('temp' + str(j) + '.pdf')
        gs.pdf2jpg('temp' + str(j)) 
        image = Image.open('temp' + str(j) + '.jpg')
        pixels = image.load()
        if anim:
            # determine data for animation
            ends = endpoints(image.size[0], image.size[1], pixels)
        else:
            ends = [image.size[1]-1]
        for i in range(len(ends)):
            # make animation
            merge_anim = PageMerge()
            merge_anim.add(pdf.pages[j])
            merge_anim.add(white)
            factor_w = merge_anim[0].w/merge_anim[1].w
            factor_h = (1-ends[i]/image.size[1])*merge_anim[0].h/merge_anim[1].h
            merge_anim[1].scale(factor_w,factor_h)  
            merge_anim_rendered = merge_anim.render()
            if not history:
                out.addpage(merge_anim_rendered)
            else:
                history_first = ((place == 'top') or (place == 'left')) and ((j>=1) or two_screens)
                horizontal = (place == 'left') or (place == 'right')
                merge_two = PageMerge()
                if history_first:
                    h = 0
                    m = 1
                else:
                    m = 0
                    h = 1
                if not history_first:
                    merge_two.add(merge_anim_rendered)
                if j>=1:
                    merge_two.add(pdf.pages[j-1])
                else:
                    merge_two.add(white)
                if history_first:     
                    merge_two.add(merge_anim_rendered)
                if j==0:
                    merge_two[h].scale(merge_two[m].w/merge_two[h].w,merge_two[m].h/merge_two[h].h)
                if horizontal:    
                    merge_two[1].x = merge_two[0].w
                else:
                    merge_two[0].y = merge_two[1].h
                out.addpage(merge_two.render())   
        remove('temp' + str(j) + '.jpg') 
        remove('temp' + str(j) + '.pdf')
    remove(name + '_flat.pdf')    
    out.write(name + add_name + '.pdf') 
    remove('white.pdf')

def make_slides_command_line():
    parser = ArgumentParser(description = "Adds line by line animations to slides in a PDF file, and displays the previous slide next to the current one")
    parser.add_argument('input', help = "name of input file (without '.pdf')")
    parser.add_argument('--rotate', help = "rotate input by the angle ROTATE", type=int, default=0)
    parser.add_argument('--nohistory', help = "do not display previous slide", action="store_true")
    parser.add_argument('--noanim', help = "do not animate line by line", action="store_true")
    parser.add_argument('--place', help = "placement of previous slide: left(default), right, top, bottom", type=str, default="left")
    parser.add_argument('--addname', help = "addition to output file name (default: '_slides')", type=str,  default="_slides")
    args = parser.parse_args()
    make_slides(args.input, rotate = args.rotate, history = not args.nohistory, anim = not args.noanim, 
                place = args.place, add_name = args.addname)
    
#if using the Python script directly the following line could be replaced by
#make_slides(filename)    
    
make_slides_command_line()



 


        
        