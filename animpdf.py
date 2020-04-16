#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version Tue 16 April 2020

@author: Sebastian Mueller
"""

from os import remove   
from os.path import isfile
from subprocess import Popen
from shutil import which
from argparse import ArgumentParser, SUPPRESS
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
        
color_tol = 120
sides_w = 50
sides_h = 5

def pixel_is_white(pixel): 
    if type(pixel) == int: 
        return pixel>=255-color_tol
    else:
        for i in range(3):
            if pixel[i]<255-color_tol:
                return False
        return True  

def line_is_white(w,h,pixels,line):
    for column in range(sides_w,w-sides_w): 
        pixel = pixels[column,line]
        if not pixel_is_white(pixel):
            return False 
    return True    

def move_until_white(w,h,pixels,start,white):
    line = start
    while line_is_white(w,h,pixels,line)!=white and line<h-sides_h: 
        line = line+1    
    return line 
    
def endpoints(w,h,pixels): 
    result = [sides_h]
    line = sides_h
    line = move_until_white(w,h,pixels,line,False) # go to start of first writing
    while (line<h-sides_h):
        line = move_until_white(w,h,pixels,line,True) # go to start of gap
        if line<h-sides_h:
            line = move_until_white(w,h,pixels,line,False) 
        result.append(line-1)
    return result

def background(w,h,pixels): 
    samples = 0
    if type(pixels[0,0])==int:
        sum = 0 
        for line in range(3*sides_h, h-3*sides_h):
            for column in range (3*sides_h, w-3*sides_w):
                pixel = pixels[column,line]
                if pixel_is_white(pixel):
                    sum += pixel
                    samples += 1
        average = int(round(sum/samples))
        return (average, average, average)
    else:
        sum = [0,0,0]
        for line in range(3*sides_h, h-3*sides_h):
            for column in range (3*sides_w, w-3*sides_w):
                pixel = pixels[column,line]
                if pixel_is_white(pixel):
                    for i in range(3):
                        sum[i] += pixel[i]
                    samples += 1
            average = [0,0,0]
            for i in range(3):
                average[i] = int(round(sum[i]/samples))  
        return tuple(average)
    
def anim_pdf(name, rotate=0, history=True, lines=True, flatten=False, place='left', add_name='_anim', two_screens=False, skip=0):
    # The optional arguments are also available as command line options and explained in anim_pdf_command_line() 
    
    # check whether file exists
    if not isfile(name + '.pdf'):
        raise Exception('File ' + name + '.pdf not found.')
    # integrate annotations (if required) and read file 
    gs = Ghostscript()
    if flatten:
        gs.flatten_pdf(name, name + '_flat')
        pdf = PdfReader(name + '_flat.pdf')
    else:
        pdf = PdfReader(name + '.pdf')
    out = PdfWriter()  
    for j in range(len(pdf.pages)-skip):
        print('slide', j+1)
        pdf.pages[j].Rotate = rotate
        # get pixels
        temp_out = PdfWriter()
        temp_out.addpage(pdf.pages[j])
        temp_out.write('temp' + str(j) + '.pdf')
        gs.pdf2jpg('temp' + str(j)) 
        image = Image.open('temp' + str(j) + '.jpg')
        pixels = image.load()
        # determine background color from first page (usually white) and create background image
        if j == 0:
            bkgr = background(image.size[0], image.size[1], pixels)
            Image.new('RGB', (1, 1), bkgr).save('white.pdf')
            white = PdfReader('white.pdf').pages[0]     
        if lines:
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
    if flatten:    
        remove(name + '_flat.pdf')    
    out.write(name + add_name + '.pdf') 
    remove('white.pdf')

def anim_pdf_command_line(): 
    parser = ArgumentParser(description = "Adds line by line animations to slides in a PDF file, and displays the previous slide next to the current one")
    parser.add_argument('input', help = "name of input file (without '.pdf')")
    parser.add_argument('--rotate', help = "rotate input by the angle ROTATE", type=int, default=0)
    parser.add_argument('--nohistory', help = "do not display previous slide", action="store_true")
    parser.add_argument('--nolines', help = "do not animate line by line", action="store_true")
    parser.add_argument('--flatten', help = "use this if PDF annotations are missing from the output", action="store_true")
    parser.add_argument('--place', help = "placement of previous slide: left(default), right, top, bottom", type=str, default="left")
    parser.add_argument('--addname', help = "addition to output file name (default: '_anim')", type=str,  default="_anim")
    # suppressed less important parameters
    parser.add_argument('--twoscreens', help = SUPPRESS, action="store_true") 
    # by default, for place=left we still start writing on the left in the beginning of the document (similar for placement=top), 
    # this may be undesired if the slides are supposed to appear on separate screens, it is deactivated by setting two_screens=True   
    parser.add_argument('--skip', help = SUPPRESS, type=int, default=0)
    # skip a number of slides in the end
    args = parser.parse_args()
    anim_pdf(args.input, rotate = args.rotate, history = not args.nohistory, lines = not args.nolines, flatten = args.flatten,
                place = args.place, add_name = args.addname, two_screens = args.twoscreens, skip = args.skip)
    
# if using the Python script directly the following line could be replaced by
# anim_pdf(filename)    
    
anim_pdf_command_line()



 


        
        